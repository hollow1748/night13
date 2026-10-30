"""Chinese pixel hotel adventure. Standard-library Tkinter interface."""
import random
import math
import json
import traceback
from datetime import datetime
import time
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont
from engine import Game, Archive, objects_for, RESIDENTS, ROLES

BG='#0d1019'; PAPER='#c4cfcc'; DIM='#72838c'; RED='#df7981'; TEAL='#81b9ae'; GOLD='#c0ac7b'
class App:
    def __init__(self,root):
        self.root=root;root.title('NIGHT 13 · English v2.7');root.geometry('1120x790');root.minsize(900,660)
        families=set(tkfont.families(root));self.font=next((f for f in ('Helvetica','Arial','DejaVu Sans') if f in families),'Arial')
        self.canvas=tk.Canvas(root,bg=BG,highlightthickness=0);self.canvas.pack(fill='both',expand=True)
        self.scene='title';self.game=Game();self.note=('', '');self.context=None;self.page=0;self.code='';self.saved=False;self.warning='';self.scale=1;self.last_tick=time.monotonic();self.last_move=0;self.scare_until=0;self.held_actions=set();self.ending_until=0
        try:self.archive=Archive(Path(__file__).resolve().parent/'user_data/endings.json')
        except (ValueError,OSError):self.archive=None;self.warning='Save unavailable. The original file is preserved; you can still play.'
        root.bind('<KeyPress>',self.key);root.bind('<KeyRelease>',lambda e:self.held_actions.discard(e.keysym.lower()));root.bind('<FocusOut>',lambda e:self.held_actions.clear());root.report_callback_exception=self.callback_error;self.canvas.bind('<Configure>',lambda e:self.render());self.canvas.focus_set();self.animate()
    def rect(self,x,y,w,h,c,outline=''):self.canvas.create_rectangle(x,y,x+w,y+h,fill=c,outline=outline)
    def text(self,x,y,s,size=12,c=PAPER,width=1000):self.canvas.create_text(x,y,text=s,font=(self.font,max(8,round(size*self.scale))),fill=c,anchor='nw',width=width*self.scale)
    def button(self,x,y,label,action):
        tag=self.canvas.create_text(x,y,text=label,font=(self.font,round(16*self.scale)),fill=TEAL,anchor='nw');self.canvas.tag_bind(tag,'<Button-1>',lambda e:action())
    def open_hub(self):
        self.scene='hub';self.render()
    def draw_identity(self):
        self.role=random.choice(list(ROLES));self.scene='identity';self.render()
    def start(self):
        self.game=Game(role=self.role);self.saved=False;self.scene='game';self.last_tick=time.monotonic();self.render()
    def result(self,result):
        if result and self.game.enraged and result[0]=='note' and result[1][0]=='Room 202 Testimony':
            self.scene='scare';self.scare_until=time.monotonic()+.65;return
        if result:self.scene,self.note=result;self.code=''
        if self.scene=='dialogue':self.context=self.note
    def write_event(self,event,**data):
        try:
            path=Path(__file__).resolve().parent/'user_data/run_events.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('a',encoding='utf-8') as stream:stream.write(json.dumps(dict(time=datetime.now().astimezone().isoformat(),event=event,**data),ensure_ascii=False)+'\n')
        except OSError:pass
    def callback_error(self,kind,error,tb):
        self.write_event('error',traceback=''.join(traceback.format_exception(kind,error,tb)))
        self.scene='pause';self.warning='An error occurred. Details were written to user_data/run_events.jsonl.'
        self.render()
    def finish(self):
        self.scene='ending'
        if not self.saved:self.ending_until=time.monotonic()+1.2
        if not self.saved:
            self.write_event('ending',ending=self.game.ending,health=self.game.health,floor=self.game.floor,steps=self.game.steps,final_rage=self.game.final_rage)
            if self.archive:
                try:self.archive.record(self.game.ending,self.game.steps,relic='master_key' in self.game.inventory)
                except OSError:self.warning='Could not save this ending. Your previous save is preserved.'
            self.saved=True
    def key(self,e):
        k=e.keysym.lower();g=self.game
        if k in ('return','space','e','q','f','j','b','escape','r','0','1','2','3'):
            if k in self.held_actions:return
            self.held_actions.add(k)
        if self.scene=='title':
            if k in ('return','space'):self.draw_identity()
            elif k=='b':self.scene='hub'
        elif self.scene=='identity':
            if k in ('return','space'):self.start()
        elif self.scene in ('ending','hub'):
            if self.scene=='ending' and time.monotonic()<self.ending_until:return
            if k=='escape':self.scene='title'
            elif k=='return':
                self.scene='title'
        elif self.scene=='pause':
            if k in ('return','escape'):self.scene='game'
            elif k=='r':self.draw_identity()
        elif self.scene=='note':
            if k in ('return','escape','e','space'):self.scene='game'
        elif self.scene in ('journal','bag'):
            if k in ('escape','j','b','e'):self.scene='game'
            elif k in ('right','d'):self.page=min(max(0,len(g.journal)-1),self.page+1)
            elif k in ('left','a'):self.page=max(0,self.page-1)
        elif self.scene=='dialogue':
            if k in ('escape','0'):self.scene='game'
            elif k in ('1','2','3'):self.result(g.dialogue(self.context,int(k)))
        elif self.scene=='code':
            if k=='escape':self.scene='game'
            elif k=='backspace':self.code=self.code[:-1]
            elif k=='return':
                if g.submit_code(self.code):self.finish()
                else:self.scene='game';self.code=''
            elif e.char and e.char in '0123456789' and len(self.code)<3:self.code+=e.char
        elif self.scene=='game':
            moves={'w':(0,-1),'up':(0,-1),'s':(0,1),'down':(0,1),'a':(-1,0),'left':(-1,0),'d':(1,0),'right':(1,0)}
            if k in moves and time.monotonic()-self.last_move>=.085:g.move(*moves[k]);self.last_move=time.monotonic()
            elif k=='e':self.result(g.interact())
            elif k=='q':self.result(g.skill())
            elif k=='f':g.flare()
            elif k=='j':self.scene='journal';self.page=0
            elif k=='b':self.scene='bag'
            elif k=='escape':self.scene='pause'
            if g.ending:self.finish()
        self.render()
    def animate(self):
        now=time.monotonic();dt=min(.25,max(0,now-self.last_tick));self.last_tick=now
        if self.scene=='scare' and now>=self.scare_until:self.scene='game'
        if self.scene=='game':
            self.game.update(dt)
            if self.game.ending:self.finish()
        self.render();self.root.after(50,self.animate)
    def panel(self,title,body,footer='[ E / Enter / Esc ] Close',colour=GOLD):
        self.rect(140,120,830,545,'#14202d','#45535d');self.rect(140,120,4,545,colour)
        self.text(175,145,'NIGHT 13 / TIME PAUSED',11,TEAL);self.text(175,185,title,21,colour,745)
        self.rect(175,237,755,1,'#3d4b55');self.text(175,260,body,14,PAPER,745);self.text(175,625,footer,11,DIM,745)
    def sprite(self,x,y,c,ghost=False):
        self.rect(x+9,y+3,11,9,c);self.rect(x+6,y+12,18,12,c);self.rect(x+6,y+23,6,4,c);self.rect(x+18,y+23,6,4,c)
        self.rect(x+11,y+7,2,2,BG);self.rect(x+18,y+7,2,2,BG)
        if ghost:self.rect(x+14,y+13,3,6,BG)
    def world(self):
        g=self.game;r=ROLES[g.role]
        # Slow, irregular lamp dips, driven by exploration time so menus pause it.
        pulse=(math.sin(g.elapsed*2.1)+.45*math.sin(g.elapsed*4.7))/1.45
        lamp=max(.25,min(1,.60+.40*pulse)) if g.final_rage else 1
        def lit(colour):
            values=[int(colour[i:i+2],16) for i in (1,3,5)]
            return '#'+''.join(f'{round(v*lamp):02x}' for v in values)
        if g.final_rage:
            self.rect(17,112,750,490,'#26141d' if lamp>.65 else '#10131d')
        self.text(28,20,'NIGHT 13',24);self.text(220,30,f'THE HOTEL / FLOOR {g.floor}',12,TEAL)
        self.text(740,26,'HUNTED! RUN' if g.hunted else 'FOOTSTEPS APPROACH' if g.hunting_ids() else {1:'FLOOR 1 / QUIET',2:'FLOOR 2 / UNEASE',3:'FLOOR 3 / THE MANAGER'}[g.floor],14,RED if g.hunted else GOLD)
        self.text(28,82,'LOCKDOWN! Everyone except the mother is hunting you. Reach the Floor 1 elevator!' if g.final_rage else 'Reading pauses pursuit. Once angered, Shen Yan follows you between floors.',11,RED if g.final_rage else DIM)
        ox,oy,t=28,125,28
        for y,row in enumerate(g.grid):
            for x,v in enumerate(row):
                visible=abs(x-g.player[0])+abs(y-g.player[1])<=g.radius;known=(g.floor,x,y) in g.seen
                c=('#35444a' if v=='#' else '#1b2930') if visible else ('#17212a' if known else '#0b1119')
                self.rect(ox+x*t,oy+y*t,27,27,lit(c))
        for pos,(kind,rid,name) in objects_for(g.floor).items():
            x,y=pos;visible=abs(x-g.player[0])+abs(y-g.player[1])<=g.radius
            if not visible and not (g.scan and kind in ('resident','evidence')):continue
            if kind=='resident' and rid in g.hunting_ids():continue
            if kind=='boss' and g.manager_awake:continue
            px,py=ox+x*t,oy+y*t
            if kind in ('resident','npc','boss'):
                self.sprite(px,py,TEAL if rid in g.resolved else (RED if kind=='boss' else GOLD));continue
            if kind in ('up','down'):
                for i in range(4):self.rect(px+3+i*5,py+22-i*5,5,3,TEAL)
            else:
                self.rect(px+5,py+9,18,16,'#695e49');self.rect(px+8,py+5,12,12,TEAL if rid in g.evidence else GOLD)
        for rid,p in g.active_hunters().items():
            if g.scan or abs(p[0]-g.player[0])+abs(p[1]-g.player[1])<=g.radius:self.sprite(ox+p[0]*t,oy+p[1]*t,RED,True)
        for p in g.blocked():self.rect(ox+p[0]*t,oy+p[1]*t,27,27,'#79664d')
        self.sprite(ox+g.player[0]*t,oy+g.player[1]*t,TEAL if not g.invulnerable else '#ffffff')
        if g.final_rage:
            for lx in (7,18):
                self.rect(ox+lx*t,oy+7,18,4,lit('#edb3a0'))
            self.text(470,82,'LIGHTS FAILING / KEEP MOVING',11,RED,280)
        self.text(44,139,f'{g.floor}01',10,DIM);self.text(397,139,f'{g.floor}02',10,DIM)
        self.text(799,125,r['name'],17,TEAL,280);self.text(799,165,f'Health {"♥ "*g.health}\nQ: {r["skill"]}\nUses: {g.skill_uses} / Matches: {g.matches}',13,PAPER,280)
        self.text(799,265,'ROLE MISSION '+('✓' if g.mission_done else 'INCOMPLETE'),14,GOLD,280);self.text(799,300,r['task'],12,PAPER,275)
        self.text(799,375,f'TESTIMONIES {len(g.resolved)} / 6',15,GOLD,280)
        for i,(rid,res) in enumerate(RESIDENTS.items()):self.text(799,415+i*25,('✓ ' if rid in g.resolved else '· ')+res['room']+' '+res['name'].split(' · ')[0],12,TEAL if rid in g.resolved else DIM,275)
        near=g.nearby();self.text(28,620,'[ E ] '+near[2][2] if near else 'Approach a resident, clue or staircase. Press E to interact.',13,TEAL)
        self.text(28,658,g.last,13,PAPER,1040)
        self.text(28,730,'WASD / Arrows: Move   E: Interact   Q: Skill   F: Match   J: Journal   B: Bag   Esc: Pause',11,DIM)
    def render(self):
        w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height());self.scale=min(w/1108,h/770)
        self.canvas.delete('all');self.rect(0,0,1108,770,BG);g=self.game
        if self.scene=='title':
            # Code-drawn title illustration; no imported image assets.
            for i in range(55):
                x=(i*173+39)%1108;y=(i*97+17)%740
                self.rect(x,y,2,2,'#26323e')
            self.rect(52,80,450,580,'#111b25','#2b3d47')
            self.rect(80,600,395,4,'#465156')
            self.rect(105,205,345,395,'#202e39')
            self.rect(120,187,315,18,'#384750')
            self.rect(213,133,132,54,'#090e15','#45505a')
            self.text(233,143,'NIGHT 13',17,RED,120)
            for row in range(3):
                for col in range(2):
                    x=142+col*173;y=240+row*101
                    light=GOLD if (row,col) in ((0,0),(1,1)) else '#0b131d'
                    self.rect(x-5,y-5,70,66,'#34434a')
                    self.rect(x,y,60,56,light);self.rect(x+28,y,4,56,'#26333d')
                    if light==GOLD:
                        self.rect(x+19,y+23,20,33,'#645b4a')
                    self.text(x+10,y+66,f'{3-row}0{col+1}',10,DIM,60)
            self.rect(249,544,61,56,'#090d14');self.rect(249,544,61,3,RED)
            self.text(184,623,'VACANCY: ONE',13,GOLD,250)
            self.text(565,106,'INSTANCE 001 / THE REGISTER',12,TEAL,490)
            self.text(559,170,'NIGHT 13',57,RED,500)
            self.rect(566,273,43,2,RED)
            self.text(566,307,'Six rooms. Six names.',21,GOLD,480)
            self.text(566,352,'A seventh line waits for yours.',18,PAPER,480)
            self.rect(565,455,457,66,'#1a2c32','#5d827b')
            hit=self.canvas.create_rectangle(565,455,1022,521,fill='#1a2c32',outline='#5d827b',tags='start_entry')
            self.button(590,473,'CHECK IN     /     ENTER',self.draw_identity)
            self.canvas.tag_bind(hit,'<Button-1>',lambda e:self.draw_identity())
            hub_hit=self.canvas.create_rectangle(565,542,1022,594,fill='#121c27',outline='#34444f')
            self.canvas.tag_bind(hub_hit,'<Button-1>',lambda e:self.open_hub())
            self.button(590,557,'THE HUB     /     B',self.open_hub)
            self.text(566,623,f'ENDING ARCHIVE  {len(self.archive.endings) if self.archive else 0} / 3',12,DIM,440)
            self.text(52,712,'NIGHT 13  /  A STORY OF NAMES AND THE WAY HOME',11,DIM,800)
        elif self.scene=='identity':
            r=ROLES[self.role];self.panel('Your Identity: '+r['name'],f'Skill: {r["skill"]} ({r["uses"]} uses)\n\n{r["ability"]}\n\n{r["task"]}\n\n{r["warning"]}\n\nPress Q inside the hotel to use your skill.', '[ Enter ] Accept identity and check in')
            self.button(175,575,'Click to check in',self.start)
        elif self.scene=='ending':
            titles={'taken':'THE MISSING GUEST','loop':'ESCAPED / THE NEXT GAME','home':'TRUE ESCAPE / THE BROKEN REGISTER'}
            body={'taken':'You never left the hotel.\nYour name appears on the seventh line.','loop':'The elevator takes you away. You found the code, but never exposed the manager.\nNo carry-over relic was earned this run.','home':'You restored six names and refused to become the seventh guest.\nThe Master Keycard has been saved to the hub if saving is available.'}
            self.panel(titles[g.ending],body[g.ending]+f'\n\n{g.steps} steps / {len(g.resolved)}/6 testimonies / Health remaining: {g.health}\n\n'+self.warning,'[ Enter / Esc ] Return to title')
        elif self.scene=='hub':
            owned=self.archive and 'master_key' in self.archive.relics
            self.panel('THE HUB','RELIC: '+('Master Keycard x 1' if owned else 'Not yet acquired')+'\n\nThe same relic does not stack across runs.\nYour keycard is saved locally and remains visible next time.\n\nThe next instance is not available yet. The keycard cannot be used or consumed here.','[ Enter / Esc ] Return to title')
        elif self.scene=='scare':
            self.rect(0,0,1108,770,'#250d15')
            self.rect(260,45,590,675,'#d6c7b7')
            self.rect(260,45,590,115,'#10121c')
            self.rect(320,235,175,65,BG);self.rect(615,235,175,65,BG)
            self.rect(390,248,28,34,RED);self.rect(670,248,28,34,RED)
            self.rect(460,420,190,220,'#170d16')
            for x in range(475,640,35):self.rect(x,420,18,35,'#e7ddcc')
            self.text(260,675,'LAUGHING AT ME TOO?!',30,RED,700)
        else:
            self.world()
            if self.scene=='note':self.panel(*self.note)
            elif self.scene=='dialogue':
                c=self.context
                choices={'resident':'1  Ask about their story\n\n2  Show the evidence from their room\n\n0  End conversation','npc':'1  Ask about the hotel rules\n\n2  Ask about your role mission\n\n3  The old photograph request\n\n0  End conversation','boss':'1  Burn the guest register\n\n2  Restore six names; refuse the seventh line\n\n3  Sign your own name\n\n0  Leave'}
                self.panel(c['title'],choices[c['kind']],'Number keys: choose / Esc: leave / Time is paused')
            elif self.scene=='journal':
                if g.journal:self.panel(*g.journal[self.page],f'Left / Right: page {self.page+1}/{len(g.journal)}    J / Esc: close')
                else:self.panel('CLUE JOURNAL','No clues yet. Evidence and conversations are recorded automatically.','J / Esc: close')
            elif self.scene=='bag':self.panel('INVENTORY',f'Matches: {g.matches}\nEvidence: {len(g.evidence)} / 6\n\n'+('\n'.join(RESIDENTS[r]['item'] for r in g.evidence) or 'No room evidence collected yet.')+'\n\n'+('Master Keycard: saved after escape' if 'master_key' in g.inventory else ''),'B / Esc: close')
            elif self.scene=='code':self.panel('Checkout Elevator','Enter the three-digit code in floor order.\n\n'+ '   '.join(self.code.ljust(3,'_')),'0-9: type / Backspace: delete / Enter: submit / Esc: back')
            elif self.scene=='pause':self.panel('PAUSED / THE NIGHT CAN WAIT','Enter / Esc: resume\n\nR: abandon this run and draw a new identity\n\nCurrent exploration is not saved. Unlocked endings and earned relics are saved locally.')
        if self.warning and self.scene=='title':self.text(52,741,self.warning,10,RED,1000)
        self.canvas.scale('all',0,0,self.scale,self.scale);self.canvas.move('all',(w-1108*self.scale)/2,(h-770*self.scale)/2)

def main():
    root=tk.Tk();App(root);root.mainloop()
if __name__=='__main__':main()
