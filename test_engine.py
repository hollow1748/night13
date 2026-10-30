import tempfile
from pathlib import Path
import unittest
from engine import Game,Archive,shortest_step,objects_for,CODE
from story import RESIDENTS,ROLES

def walk(g,target):
    for _ in range(500):
        if g.player==target:return
        p=shortest_step(g.grid,g.player,target,g.blocked())
        assert p!=g.player, target
        g.move(p[0]-g.player[0],p[1]-g.player[1]);g.update(.04)
    raise AssertionError(target)
def inspect(g,p):
    walk(g,p);return g.interact()
def complete(role,boss=True):
    g=Game(role=role);inspect(g,(8,13));inspect(g,(20,13))
    for floor in (1,2,3):
        for rid,r in RESIDENTS.items():
            if r['floor']==floor:
                inspect(g,r['evidence']);ctx=inspect(g,r['pos'])[1];g.dialogue(ctx,1);g.dialogue(ctx,2)
        if floor==2:inspect(g,(5,13))
        if floor==3:
            inspect(g,(20,13))
            if role=='mechanic':inspect(g,(5,13))
        if floor<3:inspect(g,(24,8))
    if boss:
        walk(g,g.manager_pos);g.dialogue(g.interact()[1],2)
    inspect(g,(1,8));inspect(g,(1,8));inspect(g,(12,8));assert g.submit_code(CODE)
    return g
class Tests(unittest.TestCase):
    def test_complete_all_roles(self):
        for role in ROLES:
            g=complete(role);self.assertEqual(g.ending,'home');self.assertIn('master_key',g.inventory)
    def test_no_boss(self):self.assertEqual(complete('clerk',False).ending,'loop')
    def test_no_shortcut(self):self.assertFalse(Game().submit_code(CODE))
    def test_reachability(self):
        for floor in (1,2,3):
            self.assertEqual(sum(r['floor']==floor for r in RESIDENTS.values()),2)
            for p in objects_for(floor):walk(Game(floor=floor),p)
    def test_evidence_and_no_farming(self):
        g=Game();ctx=inspect(g,(5,3))[1];g.dialogue(ctx,2);self.assertFalse(g.resolved)
        inspect(g,(8,4));ctx=inspect(g,(5,3))[1];g.dialogue(ctx,2);n=len(g.journal);g.dialogue(ctx,2)
        self.assertEqual(len(g.resolved),1);self.assertEqual(len(g.journal),n)
        inspect(g,(20,13));inspect(g,(20,13));self.assertEqual(g.matches,3)
    def test_skills(self):
        g=Game();g.skill();self.assertEqual((g.skill_uses,g.elapsed,g.scan),(2,5,10))
        g=Game(role='mechanic');g.skill();self.assertEqual(g.skill_uses,2)
        walk(g,(5,7));g.skill();self.assertFalse(g.move(0,-1));g.update(10);self.assertTrue(g.move(0,-1))
        g=Game(role='amnesiac');g.skill();self.assertEqual(g.skill_uses,3)
        walk(g,(8,5));g.skill();self.assertIn('mother',g.evidence);self.assertEqual(g.radius,2)
    def test_pursuit(self):
        g=Game(elapsed=999,player=(5,4));g.update(10);self.assertFalse(g.hunted);self.assertEqual(g.health,3)
        g=Game(floor=2,player=(20,3));ctx=g.interact()[1]
        g.dialogue(ctx,1);self.assertFalse(g.hunted)
        g.dialogue(ctx,2);self.assertFalse(g.hunted)
        g.evidence.add('actor');g.dialogue(ctx,2);self.assertTrue(g.hunted)
        self.assertIn('actor',g.resolved)
        g.invulnerable=0;g.update(.6);self.assertEqual(g.health,2)
        g.matches=1;g.flare();p=dict(g.enemies);g.update(1);self.assertEqual(g.enemies,p)
        g=Game(floor=3,player=(12,10));self.assertFalse(g.hunted);g.move(0,1);self.assertFalse(g.manager_awake)
        self.assertEqual(g.pursuit_interval,.38)
        g.boss_defeated=True;g.final_rage=True;self.assertTrue(g.hunted)
    def test_manager_chases_and_catches(self):
        g=Game(floor=3,player=(12,10),final_rage=True,boss_defeated=True);g.move(0,1)
        original=g.manager_pos
        g.update(.4);self.assertNotEqual(g.manager_pos,original)
        for _ in range(160):g.update(.1)
        self.assertEqual(g.ending,'taken')
    def test_handoff_opens_scare(self):
        from main import App
        g=Game(floor=2,player=(20,3));g.evidence.add('actor')
        result=g.dialogue(g.interact()[1],2)
        app=App.__new__(App);app.game=g;app.scene='dialogue'
        app.result(result)
        self.assertEqual(app.scene,'scare');self.assertTrue(g.hunted)
    def test_actor_follows_stairs_both_directions(self):
        g=Game(floor=1,enraged=True,invulnerable=100)
        g.enemies['actor']=(1,8)
        g.update(.61)
        self.assertEqual(g.hunter_floors['actor'],1)
        self.assertIn('actor',g.active_hunters())
        g.floor=3;g.enemies['actor']=(24,8);g.hunter_floors['actor']=2
        g.update(.4)
        self.assertEqual(g.hunter_floors['actor'],3)
    def test_final_rage_excludes_only_mother(self):
        g=Game(final_rage=True,boss_defeated=True,invulnerable=100)
        self.assertEqual(set(g.hunting_ids()),{'elder','bride','actor','doctor','child','manager'})
        self.assertNotIn('mother',g.hunting_ids())
        g.enemies['elder']=g.player;g.invulnerable=0;g.update(.01)
        self.assertEqual(g.health,2)
    def test_manager_waits_for_correct_dialogue(self):
        g=Game(floor=3,player=(12,10),role='amnesiac')
        g.move(0,1);g.update(5)
        self.assertEqual(g.manager_pos,(12,13));self.assertFalse(g.manager_awake)
        walk(g,(12,13));ctx=g.interact()[1]
        self.assertEqual(ctx['kind'],'boss')
        g.dialogue(ctx,2);self.assertFalse(g.final_rage)
        g.inventory.add('photo');g.resolved=set(RESIDENTS)
        g.dialogue(ctx,1);self.assertFalse(g.final_rage)
        g.dialogue(ctx,2);self.assertTrue(g.final_rage)
        self.assertIn('master_key',g.inventory);self.assertIn('manager',g.active_hunters())
    def test_held_enter_cannot_skip_ending(self):
        from main import App
        from types import SimpleNamespace
        app=App.__new__(App);app.scene='ending';app.game=Game();app.held_actions={'return'}
        app.key(SimpleNamespace(keysym='Return',char='\r'))
        self.assertEqual(app.scene,'ending')
    def test_ending_minimum_display(self):
        from main import App
        from types import SimpleNamespace
        import time
        app=App.__new__(App);app.scene='ending';app.game=Game();app.held_actions=set();app.ending_until=time.monotonic()+1
        app.key(SimpleNamespace(keysym='Return',char='\r'))
        self.assertEqual(app.scene,'ending')
    def test_archive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'save.json';a=Archive(p);a.record('loop',100,True);self.assertFalse(a.relics)
            a.record('home',90,True);a.record('home',110,True);b=Archive(p)
            self.assertEqual(b.best,90);self.assertEqual(b.relics,{'master_key'})
    def test_time(self):
        for n in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):Game().update(n)
if __name__=='__main__':unittest.main()
