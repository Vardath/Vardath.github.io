"""Find an installed FFmpeg pair without a recursive drive scan or executing tools.

Use the existing process PATH, then fresh Windows system/user PATH and the
exact reviewed WinGet package's conventional bin directories. No install or
environment mutation. Discovery is not evidence of functionality.
"""
import os
import shutil
from pathlib import Path

def windows_paths():
    import winreg
    for hive,key in ((winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
                     (winreg.HKEY_CURRENT_USER,r'Environment')):
        try:
            with winreg.OpenKey(hive,key) as handle:
                value,kind=winreg.QueryValueEx(handle,'Path')
            if isinstance(value,str) and len(value)<=32768:
                for part in value.split(';'):
                    part=os.path.expandvars(part.strip().strip('"'))
                    if part and Path(part).is_absolute():yield part
        except OSError:pass
    for variable in ('LOCALAPPDATA','ProgramFiles','ProgramW6432'):
        value=os.environ.get(variable)
        if not value:continue
        base=Path(value)
        if not base.is_absolute():continue
        root=(base/'Microsoft'/'WinGet'/'Packages') if variable=='LOCALAPPDATA' else (base/'WinGet'/'Packages')
        try:
            packages=sorted(root.glob('Gyan.FFmpeg_Microsoft.Winget.Source_*'))[:16]
            for package in packages:
                if not package.is_dir():continue
                yield str(package/'bin')
                for entry in sorted(package.glob('ffmpeg-*'))[:16]:
                    if entry.is_dir():yield str(entry/'bin')
        except OSError:pass

def find_pair(*,windows=None,which=None,extra_dirs=None):
    windows=os.name=='nt' if windows is None else windows
    which=which or shutil.which
    names=('ffmpeg.exe','ffprobe.exe') if windows else ('ffmpeg','ffprobe')
    def pair(directory):
        try:
            p=Path(directory)
            if not p.is_absolute():return None
            files=tuple(p/name for name in names)
            if all(x.is_file() for x in files):
                return tuple(str(x.resolve(strict=True)) for x in files)
        except (OSError,ValueError):pass
        return None
    # Require both tools from the same installation directory. A WinGet link
    # or package-manager shim may resolve to the installed executable.
    for name in names:
        found=which(name)
        if found:
            p=Path(found)
            if p.is_absolute():
                try:resolved=p.resolve(strict=True)
                except OSError:continue
                for directory in (resolved.parent,p.parent):
                    result=pair(directory)
                    if result:return result
    if windows:
        dirs=windows_paths() if extra_dirs is None else extra_dirs
        seen=set()
        for i,directory in enumerate(dirs):
            if i>=256:break
            key=str(directory).casefold()
            if key in seen:continue
            seen.add(key)
            result=pair(directory)
            if result:return result
    return None
