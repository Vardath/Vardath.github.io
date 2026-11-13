#!/usr/bin/env python3
"""Execute witnessed sampling, MD registration and bounded native publication.

Native scan actions/caps are fault-injected mocks. No engine scan, streaming or
save-file compatibility claim follows from this harness.
"""
import copy
import re
import unittest
from crystal_commerce_contracts import Obj, NULL, Returned, Continued, Broken
from passenger_completion_contracts import Seq
from survey_contracts import SurveyVM, SURVEY


class PublicationVM(SurveyVM):
    def __init__(self):
        super().__init__();self.pending=Seq();self.cursor=1;self.scan_calls=[]
        self.module.container=self.station;self.event_module=self.module;self.in_queue=False
    def remember(self,value):
        key='publication_value_'+str(len(self.vars));self.vars[key]=value;return '$'+key
    def expr(self,text):
        # Legacy native-publication scenarios have no EMP opt-in. A separate
        # source contract checks its inventory/research entitlement; this VM
        # deliberately never manufactures bombs or awards blueprints.
        if '$vgo_emp_enabled' in text and 'bomb_player_limpet_emp_01_mk1' in text:
            assert not self.state.get('vgo_emp_enabled', False)
            return False
        text=text.replace('event.param3',self.remember(self.ship))
        if self.in_queue:text=text.replace('event.param2',self.remember(self.event_module))
        text=text.replace('Init.$Pending.{$index}',self.remember(self.pending[self.vars.get('index',1)-1] if self.pending and self.vars.get('index',1)<=len(self.pending) else NULL))
        text=text.replace('Init.$Pending?', 'true').replace('Init.$Cursor?', 'true')
        text=text.replace('Init.$Pending',self.remember(self.pending)).replace('Init.$Cursor',self.remember(self.cursor))
        # Optional component fields must test actual presence, not local-var presence.
        pattern=r'@?player\.entity\.\$vgo_objects\.\{\$(module|station|leak)\}\.\$(\w+)(\?)?'
        def field(m):
            record=self.component_states.setdefault(self.vars.get(m[1],getattr(self,m[1])),{})
            return self.remember(m[2] in record if m[3] else record.get(m[2],0))
        text=re.sub(pattern,field,text)
        return super().expr(text)
    def assign(self,name,value,remove=False):
        if name=='Init.$Pending':self.pending=Seq(value);return
        if name=='Init.$Cursor':self.cursor=value;return
        if name=='Init.$Pending.{$index}':self.pending.pop(self.vars['index']-1);return
        m=re.fullmatch(r'player\.entity\.\$vgo_objects\.\{\$(module|station|leak)\}\.\$(\w+)',name)
        if m:
            record=self.component_states.setdefault(self.vars[m[1]],{})
            if remove:record.pop(m[2],None)
            else:record[m[2]]=value
            return
        super().assign(name,value,remove)
    def execute(self,nodes):
        previous=False
        for n in nodes:
            if n.tag in ['do_if','do_elseif']:
                if n.tag=='do_elseif' and previous:continue
                previous=bool(self.expr(n.get('value')))
                if previous:self.execute(n)
            elif n.tag=='do_else':
                if not previous:self.execute(n)
                previous=False
            elif n.tag=='do_all':
                for i in range(self.expr(n.get('exact'))):
                    try:self.execute(n)
                    except Continued:continue
                    except Broken:break
            elif n.tag=='set_object_scanned':
                module=self.expr(n.get('object'));self.scan_calls.append((module,self.player_cap))
                if self.scan_accepts:
                    module.scannedlevel=max(module.scannedlevel,self.player_cap)
                    module.revealedpercentage=75 if module.scannedlevel>=2 else 30
            elif n.tag=='signal_objects' and n.get('param')=="'vardath.go.survey.publish'":
                saved=dict(self.vars);self.event_module=self.expr(n.get('param2'))
                self.queue();self.vars=saved
            else:super().execute([n])
    def queue(self):
        self.in_queue=True
        try:self.execute(SURVEY.find(".//cue[@name='QueuePublication']/actions"))
        finally:self.in_queue=False
    def publish(self):self.execute(SURVEY.find(".//library[@name='PublishPending']/actions"))
    def proof(self, module=None):
        module=module or self.module;self.event_module=module
        self.component_states.setdefault(module,{})['vgo_survey_sample']={
            'ship':self.ship,'station':self.station,'started':self.age-10,'finished':self.age,'level':self.ship.maxscanlevel}
        return self.component_states[module]['vgo_survey_sample']


class DeferredNativePublication(unittest.TestCase):
    def test_real_offscreen_sampling_continues_with_negative_or_zero_player_cap(self):
        for cap in [-1,0]:
            v=PublicationVM();v.player_cap=cap
            self.assertTrue(v.run('vardath.go.survey.remote'));self.assertEqual(v.waits,11)
            self.assertEqual(v.scan_calls,[]);self.assertEqual(v.module.scannedlevel,0)
            self.assertEqual(v.pending,[v.module]);self.assertTrue(v.component_states[v.module]['vgo_survey_queued'])
            self.assertTrue(v.run('vardath.go.task.leaks'))
            self.assertTrue(any(c[0]=='add_player_discount' for c in v.native_calls))
    def test_native_cap_return_publishes_real_scan_and_removes_queue_once(self):
        v=PublicationVM();v.player_cap=0;self.assertTrue(v.run('vardath.go.survey.remote'))
        v.player_cap=2;v.ship.order=Obj('new patrol',exists=True,id='VGO_patrol');v.publish()
        self.assertEqual(v.module.scannedlevel,2);self.assertEqual(v.pending,[])
        self.assertNotIn('vgo_survey_queued',v.component_states[v.module]);v.publish()
        self.assertEqual(v.scan_calls,[(v.module,2)])
    def test_saved_queue_and_record_publish_with_same_real_component_identity(self):
        v=PublicationVM();v.player_cap=0;v.proof();v.queue()
        v.component_states=copy.deepcopy(v.component_states);v.pending=copy.deepcopy(v.pending)
        v.player_cap=2;v.publish();self.assertIs(v.scan_calls[0][0],v.module);self.assertEqual(v.pending,[])
    def test_native_partial_cap_keeps_goal_until_engine_acknowledges_full_level(self):
        v=PublicationVM();v.proof();v.queue();v.player_cap=1;v.publish()
        self.assertEqual(v.module.scannedlevel,1);self.assertEqual(v.pending,[v.module])
        self.assertNotIn('vgo_survey_level',v.component_states[v.module]);v.publish()
        self.assertEqual(len(v.scan_calls),1);v.player_cap=2;v.publish()
        self.assertEqual(v.pending,[]);self.assertEqual(v.module.scannedlevel,2)
    def test_native_refusal_backs_off_and_changed_cap_can_retry_immediately(self):
        v=PublicationVM();v.proof();v.queue();v.scan_accepts=False;v.player_cap=1
        v.publish();v.publish();self.assertEqual(len(v.scan_calls),1)
        self.assertEqual(v.component_states[v.module]['vgo_survey_publication_retry'],v.age+600)
        v.player_cap=2;v.scan_accepts=True;v.publish();self.assertEqual(v.pending,[])
        self.assertEqual(v.module.scannedlevel,2);self.assertEqual(len(v.scan_calls),2)
    def test_refused_native_action_retries_after_ten_minutes_without_false_publication(self):
        v=PublicationVM();v.proof();v.queue();v.scan_accepts=False;v.publish()
        v.age+=599;v.publish();self.assertEqual(len(v.scan_calls),1)
        v.age+=1;v.scan_accepts=True;v.publish();self.assertEqual(v.pending,[])
    def test_short_stale_distant_hostile_or_wrong_order_proof_cannot_enter_queue(self):
        for reason in ['short','stale','distance','hostile','order','owner','occupied','level','witness']:
            with self.subTest(reason=reason):
                v=PublicationVM();p=v.proof()
                if reason=='short':p['started']=v.age-9
                elif reason=='stale':p['finished']=v.age-6;p['started']=v.age-20
                elif reason=='distance':v.distance=50000
                elif reason=='hostile':v.station.hostile=True
                elif reason=='order':v.ship.order=Obj('manual',exists=True,id='MoveWait')
                elif reason=='owner':v.ship.isplayerowned=False
                elif reason=='occupied':v.occupied=True
                elif reason=='level':p['level']=3
                else:p['ship']=Obj('unrelated',exists=True)
                v.queue();self.assertEqual(v.pending,[]);self.assertEqual(v.scan_calls,[])
    def test_registration_is_idempotent_and_does_not_lower_an_earned_sample(self):
        v=PublicationVM();v.proof();v.queue();v.queue();self.assertEqual(v.pending,[v.module])
        v.ship.maxscanlevel=1;v.proof();v.queue()
        self.assertEqual(v.component_states[v.module]['vgo_survey_sample_level'],2)
    def test_round_robin_processes_sixteen_entries_without_starving_later_samples(self):
        v=PublicationVM();modules=[]
        for i in range(40):
            m=Obj('module '+str(i),exists=True,isoperational=True,scannedlevel=0,container=v.station,size=200)
            modules.append(m);v.proof(m);v.queue()
        v.scan_accepts=False;v.publish();self.assertEqual(len(v.scan_calls),16)
        v.publish();self.assertEqual(len(v.scan_calls),32);v.publish()
        self.assertEqual({m for m,cap in v.scan_calls},set(modules));self.assertEqual(len(v.scan_calls),40)
    def test_dead_module_is_removed_and_capacity_is_bounded(self):
        v=PublicationVM();v.proof();v.queue();v.module.isoperational=False;v.publish()
        self.assertEqual(v.pending,[]);self.assertEqual(v.scan_calls,[])
        v=PublicationVM();v.pending=Seq([NULL]*2048);v.proof();v.queue()
        self.assertEqual(len(v.pending),2048);self.assertFalse(v.component_states[v.module].get('vgo_survey_queued'))


if __name__=='__main__':unittest.main(verbosity=2)
