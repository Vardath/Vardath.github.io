// Offline image captioning through Florence-2; not a cloud vision service.
// Requires explicitly preinstalled files in models/onnx-community/Florence-2-base-ft.
import { Florence2ForConditionalGeneration, AutoProcessor, load_image, env } from '@huggingface/transformers';
import { resolve, join } from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
const ROOT=dirname(fileURLToPath(import.meta.url));
const ID='onnx-community/Florence-2-base-ft';
const MODEL=resolve(ROOT,'models',...ID.split('/'));
const paths=process.argv.slice(2);
if(paths.length<1 || paths.length>4 || paths.some(path=>!existsSync(path))) { console.error('Select one to four local images'); process.exit(2); }
if(!existsSync(join(MODEL,'onnx','vision_encoder_quantized.onnx')) ||
   !existsSync(join(MODEL,'config.json'))) {
  console.error('Local Florence-2 vision model is missing; approve Install Vision Model.'); process.exit(3);
}
env.allowRemoteModels=false;
env.allowLocalModels=true;
env.localModelPath=join(ROOT,'models')+'/';
env.cacheDir=join(ROOT,'cache');
const model=await Florence2ForConditionalGeneration.from_pretrained(ID,{device:'cpu',dtype:'q8'});
const processor=await AutoProcessor.from_pretrained(ID);
for(const path of paths) {
const image=await load_image(path);
const task='<MORE_DETAILED_CAPTION>';
const prompts=processor.construct_prompts(task);
const inputs=await processor(image,prompts);
const ids=await model.generate({...inputs,max_new_tokens:120});
const words=processor.batch_decode(ids,{skip_special_tokens:false})[0];
const result=processor.post_process_generation(words,task,image.size);
const caption=result?.[task];
if(typeof caption!=='string' || !caption.trim()) throw new Error('Caption model returned no description');
console.log('IMAGE_CAPTION_JSON: '+JSON.stringify({caption,image:path}));

}
