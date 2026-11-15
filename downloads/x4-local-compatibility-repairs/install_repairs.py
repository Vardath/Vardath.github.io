"""Apply version-checked X4 script repairs. Run with GAME_FOLDER --apply; default is check-only."""
from pathlib import Path
import argparse,json,hashlib,re,zipfile,time
def sha(b):return hashlib.sha256(b).hexdigest()
def catalog_entries(cat):
 data=cat.with_suffix('.dat').read_bytes();off=0;entries=[]
 for line in cat.read_text(encoding='utf-8').splitlines():
  path,n,stamp,md5=line.rsplit(' ',3);n=int(n);b=data[off:off+n];off+=n
  assert hashlib.md5(b).hexdigest()==md5,f'Archive checksum mismatch: {cat}/{path}'
  entries.append((path,b,stamp))
 assert off==len(data),f'Archive length mismatch: {cat}'
 return entries
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('game',type=Path);ap.add_argument('--apply',action='store_true');ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parent);args=ap.parse_args()
 root=(args.game/'extensions').resolve();assert root.is_dir(),'Game extensions folder not found'
 package=args.package.resolve();manifest=json.loads((package/'repairs.json').read_text());changes={};skipped=[];checked=0
 for mod in sorted({r['mod'] for r in manifest}):
  folder=(root/mod).resolve();assert folder.parent==root
  if not folder.is_dir():skipped.append(mod);continue
  rows=[r for r in manifest if r['mod']==mod];cats={};owners={}
  for cat in sorted(folder.glob('*.cat')):
   if not re.fullmatch(r'(ext|subst)_\d+\.cat',cat.name):continue
   entries=catalog_entries(cat);cats[cat]=entries
   for path,b,stamp in entries:owners[path.replace('\\','/')]=(cat,b)
  updates={}
  for row in rows:
   rel=row['file'];p=(folder/rel).resolve();assert p.is_relative_to(folder)
   current=p.read_bytes() if p.is_file() else owners.get(rel,(None,None))[1]
   new=(package/'files'/mod/rel).read_bytes();assert sha(new)==row['after']
   if current==new:checked+=1;continue
   assert (current is None and row['allow_missing']) or (current is not None and sha(current) in row['accepted_before']),f'Unsupported or edited source: {mod}/{rel}; no files written'
   checked+=1
   if p.is_file() or rel not in owners:changes[p]=new
   else:updates[rel]=new
  for cat,entries in cats.items():
   selected={rel:b for rel,b in updates.items() if owners[rel][0]==cat}
   if not selected:continue
   blobs=[];lines=[]
   for path,b,stamp in entries:
    rel=path.replace('\\','/')
    if rel in selected:b=selected[rel];stamp=str(int(time.time()))
    blobs.append(b);lines.append(f'{path} {len(b)} {stamp} {hashlib.md5(b).hexdigest()}\n')
   changes[cat]=''.join(lines).encode();changes[cat.with_suffix('.dat')]=b''.join(blobs)
 print(f'Checked {checked} script files; {len(changes)} filesystem changes; absent mods skipped: {", ".join(skipped) or "none"}')
 if not args.apply or not changes:return
 backup=package/f'Before_Repairs_{time.time_ns()}.zip'
 with zipfile.ZipFile(backup,'w',zipfile.ZIP_DEFLATED) as z:
  absent=[]
  for p in changes:
   if p.exists():z.write(p,p.relative_to(root).as_posix())
   else:absent.append(p.relative_to(root).as_posix())
  z.writestr('NEW_FILES.json',json.dumps(absent))
 for p,b in changes.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 for p,b in changes.items():assert p.read_bytes()==b
 print(f'Installed and verified repairs. Backup: {backup}. Restart X4.')
if __name__=='__main__':main()
