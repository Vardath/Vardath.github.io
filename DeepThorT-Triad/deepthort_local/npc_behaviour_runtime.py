"""Portable deterministic grid NPC patrol/pursuit controller; standard library only."""
from collections import deque

def route(start,target,w,h,walls):
    previous={start:None};q=deque([start])
    while q:
        p=q.popleft()
        if p==target:
            path=[]
            while previous[p] is not None:
                path.append(p);p=previous[p]
            return list(reversed(path))
        x,y=p
        for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=n[0]<w and 0<=n[1]<h and n not in walls and n not in previous:
                previous[n]=p;q.append(n)
    return None

class Controller:
    """Call step once per game tick with the current player grid cell or None."""
    def __init__(self,spec):
        level=spec['level']
        self.w,self.h=level['width'],level['height']
        self.walls=set(map(tuple,level['walls']))
        self.patrol=list(map(tuple,spec['patrol']))
        self.position=self.patrol[0]
        self.waypoint=1%len(self.patrol)
        self.radius=spec['detection_distance']
        self.mode='patrol'

    def step(self,player):
        if player is not None:
            player=tuple(player)
            if len(player)!=2 or any(type(v) is not int for v in player) or not (0<=player[0]<self.w and 0<=player[1]<self.h) or player in self.walls:
                raise ValueError('Invalid player cell')
        path=route(self.position,player,self.w,self.h,self.walls) if player is not None else None
        if path is not None and len(path)<=self.radius:
            self.mode='pursuit'
            # Stop adjacent rather than walking onto the player.
            if len(path)>1:self.position=path[0]
        else:
            if self.mode=='pursuit':self.mode='return'
            target=self.patrol[self.waypoint]
            path=route(self.position,target,self.w,self.h,self.walls)
            if path is None:raise ValueError('Unreachable patrol target')
            if path:self.position=path[0]
            if self.position==target:
                self.waypoint=(self.waypoint+1)%len(self.patrol)
                self.mode='patrol'
        return {'position':list(self.position),'mode':self.mode,'next_waypoint':self.waypoint}
