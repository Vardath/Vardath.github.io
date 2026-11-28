"""Two automatic profiles. The root commit limit is never shrunk under live workers."""
from dataclasses import dataclass

GIB=1024**3
MEDIUM_CPU=50
MEDIUM_RAM=65
MEDIUM_RESERVE=15
HIGH_CPU=85
HIGH_RAM=80
HIGH_RESERVE=10

@dataclass
class AutomaticResources:
    """Immediate protection, two clear samples before returning to High."""
    medium: bool=False
    clear_samples: int=0
    def choose(self,gaming,available,total):
        if (type(gaming) is not bool or type(available) is not int or type(total) is not int
                or total<=0 or not 0<=available<=total):
            gaming=True;available=0;total=1
        if gaming or available*100<total*MEDIUM_RESERVE:
            self.medium=True
            self.clear_samples=0
        elif self.medium:
            if available*100>=total*20:
                self.clear_samples+=1
                if self.clear_samples>=2:
                    self.medium=False
                    self.clear_samples=0
            else:self.clear_samples=0
        return MEDIUM_CPU if self.medium else HIGH_CPU

def admission_budget(cap,available,total,cpu_rate):
    """Translate observed hard limits into the effective cooperative budget.
    The returned available figure accounts for Medium's additional 5% reserve;
    existing consumers already retain 10%. Never advertise more than the OS cap.
    """
    if any(type(v) is not int for v in (cap,available,total,cpu_rate)) or not (
            0<cap<=total and 0<=available<=total and 0<cpu_rate<=HIGH_CPU*100):
        raise ValueError('Invalid supervised resource sample')
    if cpu_rate<=MEDIUM_CPU*100:
        return min(cap,total*MEDIUM_RAM//100),max(0,available-total*(MEDIUM_RESERVE-HIGH_RESERVE)//100),total
    return cap,available,total

def managed_slots(sample):
    from .adaptive_admission import capacity
    cap,available,total,cpu_rate=sample
    slots=capacity(admission_budget(cap,available,total,cpu_rate))
    return min(1,slots) if cpu_rate<=MEDIUM_CPU*100 else slots

def game_library_path(path):
    """Conservative known game-library paths; not a universal game classifier."""
    if not isinstance(path,str):return False
    p=path.replace('/','\\').casefold()
    name=p.rsplit('\\',1)[-1]
    if not name.endswith('.exe') or name in {
        'steam.exe','steamwebhelper.exe','epicgameslauncher.exe','epicwebhelper.exe',
        'galaxyclient.exe','galaxyclient helper.exe','gog galaxy.exe','unins000.exe'}:
        return False
    return any(part in p for part in ('\\steamapps\\common\\','\\epic games\\','\\gog games\\','\\xboxgames\\'))
