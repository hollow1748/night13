"""Three-floor hotel rules, timed pursuit, identity skills and persistent rewards."""
from collections import deque
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import random
from story import RESIDENTS, ROLES, RULES
WIDTH,HEIGHT=26,17
START=(12,8)
DOORS=((5,6),(20,6))
CODE='257'

def make_map():
    grid=[['.' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x in (0,25) or y in (0,16):grid[y][x]='#'
    for x in range(1,25):grid[6][x]=grid[10][x]='#'
    for x,y in DOORS:grid[y][x]='.'
    grid[10][12]='.'
    for y in range(1,6):grid[y][12]='#'
    return grid

def shortest_step(grid,start,goal,blocked=()):
    queue=deque([(start,None)]);seen={start};blocked=set(blocked)
    while queue:
        p,first=queue.popleft()
        if p==goal:return first or start
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n=(p[0]+dx,p[1]+dy)
            if 0<=n[0]<WIDTH and 0<=n[1]<HEIGHT and grid[n[1]][n[0]]!='#' and n not in seen and n not in blocked:
                seen.add(n);queue.append((n,first or n))
    return start

def objects_for(floor):
    result={}
    for rid,r in RESIDENTS.items():
        if r['floor']==floor:
            result[r['pos']]=('resident',rid,r['name'])
            result[r['evidence']]=('evidence',rid,r['item'])
    result[(1,8)]=('down','','Stairs Down' if floor>1 else 'Sealed Entrance')
    result[(24,8)]=('up','','Stairs Up' if floor<3 else 'Sealed Rooftop')
    if floor==1:
        result.update({(12,8):('exit','','Checkout Elevator'),(4,13):('npc','','Night Attendant'),
                       (20,13):('supplies','','Candle and Matches'),(3,8):('rules','','Reception Rules'),
                       (8,13):('handover','','Handover Book')})
    elif floor==2:result[(5,13)]=('toolbox','','Maintenance Toolbox')
    else:result.update({(5,13):('power','','Floor 3 Power Box'),(20,13):('photo','','Your Old Photograph'),(12,13):('boss','','Hotel Manager')})
    return result

@dataclass
class Game:
    role: str='clerk'
    grid: list=field(default_factory=make_map)
    player: tuple=START
    floor: int=1
    inventory: set=field(default_factory=set)
    evidence: set=field(default_factory=set)
    resolved: set=field(default_factory=set)
    seen: set=field(default_factory=set)
    journal: list=field(default_factory=list)
    steps: int=0
    elapsed: float=0.0
    duration: float=180.0
    health: int=3
    matches: int=0
    ward: float=0.0
    skill_uses: int=-1
    scan: float=0.0
    narrow: float=0.0
    invulnerable: float=0.0
    blocks: dict=field(default_factory=dict)
    enemies: dict=field(default_factory=dict)
    enemy_clock: float=0.0
    hunter_floors: dict=field(default_factory=dict)
    final_rage: bool=False
    enraged: bool=False
    manager_awake: bool=False
    manager_pos: tuple=(12,13)
    boss_defeated: bool=False
    ending: str=''
    last: str='Speak to the night attendant in the lower-left part of the lobby.'

    def __post_init__(self):
        if self.role not in ROLES:raise ValueError('Unknown identity')
        if self.skill_uses<0:self.skill_uses=ROLES[self.role]['uses']
        if not self.enemies:self.enemies={rid:r['pos'] for rid,r in RESIDENTS.items()}
        if not self.hunter_floors:self.hunter_floors={rid:r['floor'] for rid,r in RESIDENTS.items()}|{'manager':3}
        self.reveal()
    @property
    def hunted(self):return bool(self.active_hunters())
    def hunting_ids(self):
        if self.final_rage:return [rid for rid in RESIDENTS if rid!='mother']+['manager']
        return ['actor'] if self.enraged else []
    def active_hunters(self):
        return {rid:(self.manager_pos if rid=='manager' else self.enemies[rid]) for rid in self.hunting_ids() if self.hunter_floors[rid]==self.floor}
    @property
    def pursuit_interval(self):return .38 if self.floor==3 else .60
    @property
    def remaining(self):return max(0,int(math.ceil(self.duration-self.elapsed)))
    @property
    def mission_done(self):
        if self.role=='clerk':return 'handover' in self.inventory and len(self.resolved)==6
        if self.role=='mechanic':return 'power' in self.inventory
        return 'photo' in self.inventory
    @property
    def radius(self):return 2 if self.narrow else 6
    def log(self,title,body):
        if not any(t==title for t,b in self.journal):self.journal.append((title,body))
        return 'note',(title,body)
    def reveal(self):
        x,y=self.player
        for yy in range(max(0,y-self.radius),min(HEIGHT,y+self.radius+1)):
            for xx in range(max(0,x-self.radius),min(WIDTH,x+self.radius+1)):
                if abs(xx-x)+abs(yy-y)<=self.radius:self.seen.add((self.floor,xx,yy))
    def blocked(self):return {p for (f,p),ttl in self.blocks.items() if f==self.floor and ttl>0}
    def update(self,seconds):
        if self.ending:return
        if not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<0:raise ValueError('Invalid time interval')
        was_hunted=self.hunted;self.elapsed+=seconds
        for name in ('ward','scan','narrow','invulnerable'):setattr(self,name,max(0,getattr(self,name)-seconds))
        self.blocks={k:v-seconds for k,v in self.blocks.items() if v>seconds}
        if not was_hunted and self.hunted:self.last='The hunt has begun!'
        if not self.hunting_ids() or self.ward:return
        self.enemy_clock+=seconds
        # The UI supplies short intervals. Bound catch-up after external suspension.
        for _ in range(min(3,int(self.enemy_clock/self.pursuit_interval))):
            self.enemy_clock-=self.pursuit_interval
            for rid in self.hunting_ids():
                p=self.manager_pos if rid=='manager' else self.enemies[rid]
                floor=self.hunter_floors[rid]
                follows=rid!='manager' or self.final_rage
                if floor!=self.floor:
                    if not follows:continue
                    going_up=floor<self.floor
                    stair=(24,8) if going_up else (1,8)
                    if p==stair:
                        self.hunter_floors[rid]+=1 if going_up else -1
                        nxt=(2,8) if going_up else (23,8)
                        if self.hunter_floors[rid]==self.floor:self.last='Footsteps on the stairs. It has followed you to this floor!'
                    else:
                        blocks={pos for (f,pos),ttl in self.blocks.items() if f==floor and ttl>0}
                        nxt=shortest_step(self.grid,p,stair,blocks)
                else:nxt=shortest_step(self.grid,p,self.player,self.blocked())
                if rid=='manager':self.manager_pos=nxt
                else:self.enemies[rid]=nxt
            self.check_contact()
        self.check_contact()
    def check_contact(self):
        if self.ending or self.invulnerable or self.ward:return
        if self.hunted and self.player in self.active_hunters().values():
            self.health-=1;self.invulnerable=3;self.last='An icy hand touches you. Run! You have three seconds of protection.'
            if self.health<=0:self.ending='taken'
    def move(self,dx,dy):
        if self.ending or (dx,dy) not in ((1,0),(-1,0),(0,1),(0,-1)):return False
        n=(self.player[0]+dx,self.player[1]+dy)
        if not (0<=n[0]<WIDTH and 0<=n[1]<HEIGHT) or self.grid[n[1]][n[0]]=='#' or n in self.blocked():
            self.last='You cannot pass. Your barricades block you too.';return False
        self.player=n;self.steps+=1
        self.reveal();self.check_contact();return True
    def nearby(self):
        choices=[(abs(p[0]-self.player[0])+abs(p[1]-self.player[1]),p,obj) for p,obj in objects_for(self.floor).items()]
        if self.manager_awake:
            choices=[c for c in choices if c[2][0]!='boss']
            if self.hunter_floors['manager']==self.floor:
                p=self.manager_pos
                choices.append((abs(p[0]-self.player[0])+abs(p[1]-self.player[1]),p,('boss','','Hotel Manager')))
        # During pursuit a resident is at their current position, not their empty room.
        if self.hunting_ids():
            choices=[c for c in choices if c[2][0]!='resident' or c[2][1] not in self.hunting_ids()]
            choices += [(abs(p[0]-self.player[0])+abs(p[1]-self.player[1]),p,('resident',rid,RESIDENTS[rid]['name'])) for rid,p in self.enemies.items() if rid in self.active_hunters()]
        near=min(choices,key=lambda c:(c[0],c[1]),default=None)
        return near if near and near[0]<=1 else None
    def interact(self):
        if self.ending:return None
        near=self.nearby()
        if not near:self.last='Approach an object, resident or staircase and press E.';return None
        kind,rid,name=near[2]
        if kind=='resident':return 'dialogue',dict(kind='resident',id=rid,title=name)
        if kind=='npc':return 'dialogue',dict(kind='npc',title='Night Attendant')
        if kind=='boss':return 'dialogue',dict(kind='boss',title='The Manager · The Seventh Line')
        if kind in ('up','down'):
            target=self.floor+(1 if kind=='up' else -1)
            if not 1<=target<=3:self.last='There is nothing beyond the door but a damp wall.';return None
            self.floor=target;self.player=(2,8) if kind=='up' else (23,8)
            self.invulnerable=max(2,self.invulnerable);self.reveal();self.last=f'You have reached Floor {target}.';return None
        if kind=='evidence':
            self.evidence.add(rid);return self.log(RESIDENTS[rid]['item'],RESIDENTS[rid]['proof'])
        if kind=='rules':return self.log('Reception Rules',RULES)
        if kind=='supplies':
            if 'candle' not in self.inventory:self.inventory.add('candle');self.matches+=3
            return self.log('A Little Warmth','You take a candle and three matches.\nPress F to freeze all pursuers for seven seconds.\nReading clues pauses the chase.')
        if kind=='handover':
            self.inventory.add(kind);return self.log('The Seventh Line','The first six lines belong to residents. The seventh is empty.\nThe manager wants your signature, but you never checked in.\nOnly returning the true names can break his rules.')
        if kind=='toolbox':
            self.inventory.add(kind);return self.log('Maintenance Tools','You take the toolbox.\nThe Maintenance Worker can repair the Floor 3 power box with it. Other identities have different missions.')
        if kind=='power':
            if self.role!='mechanic':return self.log('Power Box','Only the Maintenance Worker can repair this circuit. Your identity has a different mission.')
            if 'toolbox' not in self.inventory:self.last='You need the toolbox from Floor 2 first.';return None
            self.inventory.add('power');return self.log('Power Restored','You cut the black wire leading to the office and reconnect the elevator circuit.\nMaintenance Worker mission complete.')
        if kind=='photo':
            self.inventory.add(kind);return self.log('Your Own Photograph','It is you, standing outside the hotel.\nOn the back: "You were only passing by. You are not the seventh guest."\nAmnesiac Guest mission complete.')
        if kind=='exit':
            if len(self.resolved)<6:self.last='You still need testimonies. Six stories hide the digits and their order.';return None
            if not self.mission_done:self.last='Complete the role mission shown on the right first.';return None
            return 'code',('Checkout Elevator','Use the six residents\' clues to arrange three digits in floor order.')
        return None
    def dialogue(self,context,choice):
        """Resolve numbered dialogue choices; no item can be farmed repeatedly."""
        if self.ending:return None
        near=self.nearby()
        if not near or near[2][0]!=context['kind'] or (context['kind']=='resident' and near[2][1]!=context.get('id')):
            raise ValueError('Move closer to the person you want to speak to.')
        kind=context['kind']
        if kind=='resident':
            rid=context['id'];r=RESIDENTS[rid]
            if choice==1:return self.log(r['name'],r['intro'])
            if choice==2:
                if rid not in self.evidence:
                    return 'note',('Missing Evidence',f'Inspect {r["item"]} in Room {r["room"]}, then return to show it.')
                if rid in self.resolved:
                    if rid=='actor':return 'note',('He Is Still Hunting You','You already gave him the photographs. He trusts no one outside the mirror. He will follow you on the stairs. Run!')
                    return 'note',('A Moment of Peace',r['clue'])
                self.resolved.add(rid);self.last=f'Room {r["room"]} testimony collected.'
                if rid=='actor':return self.anger_actor(r['resolution']+'\n\n'+r['clue'])
                return self.log(f'Room {r["room"]} Testimony',r['resolution']+'\n\n'+r['clue'])
            return None
        if kind=='npc':
            if choice==1:return self.log('The Attendant\'s Warning',RULES)
            if choice==2:return 'note',(ROLES[self.role]['name']+': Your Mission',ROLES[self.role]['task']+'\n\n'+ROLES[self.role]['warning'])
            if choice==3:
                if 'photo' not in self.inventory:return 'note',('The Attendant\'s Request','An old photograph lies in the staff area on Floor 3. Bring it to me and I will give you a match.')
                if 'npc_reward' not in self.inventory:self.matches+=1;self.inventory.add('npc_reward')
                return self.log('The Attendant\'s Truth','You receive one match (once per run).\n"The manager does not own the exit. When the six residents remember their names, his rules can be broken."')
            return None
        if kind=='boss':
            if self.boss_defeated:return 'note',('The Hotel Is in Lockdown','You have the keycard! Everyone except the mother is hunting you. Reach the Floor 1 elevator and enter the code!')
            if len(self.resolved)<6 or not self.mission_done:return 'note',('The Seventh Line Is Still Empty','The manager slides the register towards you. "Finish your duties before asking to check out."\nYou need all six testimonies and your completed role mission.')
            if choice==2:
                self.boss_defeated=True;self.final_rage=True;self.manager_awake=True;self.enemy_clock=0
                self.invulnerable=max(self.invulnerable,3);self.inventory.add('master_key')
                self.last='The manager erupts! Everyone except the mother is hunting you. Take the keycard to the Floor 1 elevator!'
                return self.log('The Manager\'s Master Keycard','You speak the six true names and refuse to sign the seventh line.\nThe manager\'s face turns blank. He tears the register apart. Red lights flood the hotel.\nEvery resident except the mother in Room 101 joins the hunt. The manager lunges too.\nThey can follow you between floors. Escape through the Floor 1 elevator!\n\nYou take the only carry-over relic: the Master Keycard.\nIt is saved to the hub only after you escape. It is not consumed here.')
            self.elapsed+=20;self.last='The manager smiles. Your run clock advances by 20 seconds.'
            return 'note',('The Wrong Rule','Burning the names or registering yourself only preserves his power.\nThe child\'s drawing and the handover book explain how to confront him.')
        return None
    def anger_actor(self,body):
        self.enraged=True;self.enemy_clock=0;self.invulnerable=max(self.invulnerable,3)
        self.last='Shen Yan is furious! Matches can stop him briefly, but he follows you between floors.'
        return self.log('Room 202 Testimony' if 'actor' in self.resolved else 'Shen Yan\'s Fury',body+'\n\nHe tears the photographs. "You are laughing at me too!"\nHe lunges as soon as you hand them over. Press F to use a match and run!\nCollecting his testimony does not stop him. He can follow you to Floors 1 and 3. Save your matches and find the exit.')
    def skill(self):
        if self.ending:return None
        if not self.skill_uses:self.last='No skill uses remain this run.';return None
        if self.role=='clerk':
            self.skill_uses-=1;self.scan=10;self.elapsed+=5;self.last='Room Register: this floor\'s residents and evidence are marked for 10 seconds. Run clock +5 seconds.'
        elif self.role=='mechanic':
            door=min(DOORS,key=lambda p:abs(p[0]-self.player[0])+abs(p[1]-self.player[1]))
            if abs(door[0]-self.player[0])+abs(door[1]-self.player[1])>1:self.last='Stand beside a guest-room doorway, then press Q to barricade it.';return None
            if (self.floor,door) in self.blocks:self.last='This doorway is already barricaded.';return None
            self.skill_uses-=1;self.blocks[(self.floor,door)]=10;self.last='Doorway sealed for 10 seconds. Neither you nor the pursuers can pass.'
        else:
            choices=[(abs(r['evidence'][0]-self.player[0])+abs(r['evidence'][1]-self.player[1]),rid) for rid,r in RESIDENTS.items() if r['floor']==self.floor and rid not in self.evidence]
            distance,rid=min(choices,default=(999,''))
            if distance>3:self.last='No undiscovered evidence nearby. Move closer to a room\'s clue and press Q.';return None
            self.skill_uses-=1;self.narrow=10;self.evidence.add(rid);self.reveal()
            return self.log('Memory Echo / '+RESIDENTS[rid]['item'],RESIDENTS[rid]['proof']+'\n\nCost: reduced sight for the next 10 seconds.')
        self.reveal();return None
    def flare(self):
        if not self.matches:self.last='No matches. Find supplies in the Floor 1 staff area or help the attendant.';return False
        if self.ending:return False
        self.matches-=1;self.ward=7;self.last='The flame protects you. All pursuit pauses for seven seconds.';return True
    def submit_code(self,code):
        if self.ending:return False
        near=self.nearby()
        if not near or near[2][0]!='exit' or len(self.resolved)<6 or not self.mission_done:return False
        if code.strip()!=CODE:self.last='Wrong code. Each floor has two clues that confirm its digit. Check your journal.';return False
        self.ending='home' if self.boss_defeated else 'loop';return True

class Archive:
    """Legacy-compatible ending archive plus one persistent boss relic."""
    def __init__(self,path):
        self.path=Path(path);self.endings=set();self.best=None;self.relics=set()
        if self.path.exists():
            data=json.loads(self.path.read_text(encoding='utf-8'))
            if (not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('endings'),list)
                or any(e not in ('taken','loop','home') for e in data['endings'])
                or not isinstance(data.get('relics',[]),list) or any(r!='master_key' for r in data.get('relics',[]))
                or (data.get('best') is not None and (type(data['best']) is not int or data['best']<0))):raise ValueError('Invalid save format. The original file has been preserved.')
            self.endings=set(data['endings']);self.best=data.get('best');self.relics=set(data.get('relics',[]))
    def record(self,ending,steps,relic=False):
        if ending not in ('taken','loop','home') or type(steps) is not int or steps<0:raise ValueError('Invalid ending record')
        endings=self.endings|{ending};best=self.best;relics=self.relics.copy()
        if ending!='taken':best=steps if best is None else min(best,steps)
        if ending=='home' and relic:relics.add('master_key')
        self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(version=1,endings=sorted(endings),best=best,relics=sorted(relics)),ensure_ascii=False,indent=2),encoding='utf-8')
        tmp.replace(self.path);self.endings=endings;self.best=best;self.relics=relics
