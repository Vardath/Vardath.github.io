"""Scene-asset acceptance: deterministic stock metadata fixtures and real capped decoder."""
import hashlib
import struct
import tempfile
import zlib
from pathlib import Path
from . import stock_images
from .video_planning import binding
from .video_visuals import assign,status,inspect,normalize

def fixture_png():
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    # A real 8x8 RGB test image; not generated artwork.
    raw=b''.join(b'\0'+bytes((i*30,70,180))*8 for i in range(8))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',8,8,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

def scenario():
    request={'id':9,'project':'fixture-project','chat_id':'fixture-chat','prompt':'/video A garden illustration'}
    row={'narration':'A flower opens.','visual':'A garden flower','asset_source':'either','research_needed':[]}
    plan={'schema':'deepthort-video-plan-v1','binding':binding(request),
          'outline':{'title':'Garden','audience':'All','language':'English','style':'Quiet','aspect':'16:9',
          'target_seconds':30,'scenes':[{'title':'A','intent':'A'},{'title':'B','intent':'B'},{'title':'C','intent':'C'}]},
          'scripts':[{'scene':i,**row} for i in (1,2,3)],'status':'reviewed_draft','rendered':False,
          'assets_acquired':False,'audio_generated':False}
    return request,plan

def page(ident=7,license='CC BY 4.0',link='https://creativecommons.org/licenses/by/4.0/',host='upload.wikimedia.org'):
    data=fixture_png()
    return {'pageid':ident,'title':'File:Garden.png','index':1,'imageinfo':[{
        'mime':'image/png','size':len(data),'width':8,'height':8,'sha1':hashlib.sha1(data).hexdigest(),
        'url':'https://'+host+'/wikipedia/commons/a/ab/Garden.png',
        'descriptionurl':'https://commons.wikimedia.org/wiki/File:Garden.png',
        'extmetadata':{'LicenseShortName':{'value':license},'LicenseUrl':{'value':link},
            'Artist':{'value':'<a>Fixture artist</a>'},'Credit':{'value':'Fixture credit'},
            'ImageDescription':{'value':'Garden flower'}}}]}

def exercise(native=False,cancelled=None):
    data=fixture_png();request,plan=scenario()
    options=stock_images.candidates({'query':{'pages':{'7':page(),
        '8':page(8,'CC BY-SA 4.0','https://creativecommons.org/licenses/by-sa/4.0/'),
        '9':page(9,host='other.example'),'10':page(10,link='https://other.example/license')}}})
    if len(options)!=1 or options[0]['id']!=7 or options[0]['creator']!='Fixture artist':
        raise ValueError('Stock candidate filtering failed')
    from unittest.mock import patch
    with patch('deepthort_local.stock_images.get',return_value=data):
        if stock_images.download(options[0])!=data:raise ValueError('Stock digest verification failed')
    with patch('deepthort_local.stock_images.get',return_value=data[:-1]+b'X'):
        try:stock_images.download(options[0])
        except ValueError:pass
        else:raise ValueError('Changed source image accepted')
    with tempfile.TemporaryDirectory(prefix='triad-visual-test-') as temp:
        folder=Path(temp);original=folder/'original.png';original.write_bytes(data)
        calls=[]
        def decode(raw,dest,cancel=None):
            calls.append('decode')
            if native:return normalize(raw,dest,cancel)
            # Pure fixture only, not a claim of real native decoding.
            dest.write_bytes(raw);return inspect(dest)
        def generator(description,cancel=None):
            calls.append('generate')
            return data,{'engine':'fixture','rights_status':'fixture only','illustration':True}
        def search(description,cancel=None):
            calls.append('search');return options
        def download(candidate,cancel=None):
            calls.append('download');return data
        def select(row,offered):return 7
        kw=dict(searcher=search,downloader=download,select=select,normalizer=decode,cancelled=cancelled)
        try:assign(folder,request,plan,1,'stock',review=lambda *a:False,**kw)
        except ValueError:pass
        else:raise ValueError('Rejected stock candidate accepted')
        if 'download' in calls:raise ValueError('Stock acquired before review')
        asset=assign(folder,request,plan,1,'stock',review=lambda *a:True,**kw)
        if asset['source']['candidate']['license']!='CC BY 4.0':raise ValueError('License receipt missing')
        assign(folder,request,plan,2,'provided',provided=original,normalizer=decode,cancelled=cancelled)
        partial,_=status(folder,request,plan)
        if partial['missing']!=[3]:raise ValueError('Partial asset status wrong')
        assign(folder,request,plan,3,'generate',generator=generator,normalizer=decode,cancelled=cancelled)
        all_assets,root=status(folder,request,plan)
        if all_assets['missing'] or all_assets['publication_rights_verified'] or all_assets['rendered']:
            raise ValueError('Invalid finished asset status')
        before=list(calls)
        if assign(folder,request,plan,1,'stock',review=lambda *a:True,**kw)!=asset or calls!=before:
            raise ValueError('Cached scene was acquired again')
        try:assign(folder,request,plan,2,'generate',generator=generator,normalizer=decode,cancelled=cancelled)
        except ValueError:pass
        else:raise ValueError('Existing image was overwritten')
        try:assign(folder,request,plan,1,'stock',cancelled=lambda:True,review=lambda *a:True,
                   searcher=search,downloader=download,select=select,normalizer=decode)
        except ValueError:pass
        else:raise ValueError('Cancelled acquisition continued')
        (root/'scene-01'/'image.png').write_bytes(b'bad')
        try:status(folder,request,plan)
        except ValueError:pass
        else:raise ValueError('Damaged stored visual accepted')
    return {'status':'passed','detail':('Actual capped Windows PNG decode and normalization; ' if native else 'Synthetic normalization fixture; ')+
        'stock license and host filtering, source digest, rejected-candidate refusal, scene assignment, partial/resume, supplied/generated fixture and stale-image checks passed. No live stock network call or diffusion inference.'}

def native_exercise(cancelled=None):
    return exercise(native=True,cancelled=cancelled)
