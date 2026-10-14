import random, json, csv, math, datetime as dt
random.seed(7)
ASOF=dt.date(2026,9,30)
def mstart(y,m): return dt.date(y,m,1)
def addm(d,n):
    y=d.year+(d.month-1+n)//12; m=(d.month-1+n)%12+1; return dt.date(y,m,1)
months=[addm(dt.date(2023,1,1),i) for i in range(45)]  # Jan23..Sep26
ret={m:random.gauss(0.006,0.028) for m in months}
CH={ # id: (label, annual funded approx, ticket median, series, intermediary prefix)
 'website':('Website (direct)',16,350000,'B',None),
 'referral':('Referral (direct)',12,800000,'C',None),
 'ria':('RIA advisers',26,250000,'D','RIA'),
 'broker':('Broker-dealer agents',20,150000,'A','BD'),
 'platform':('Alt platforms',10,200000,'A','PLT'),
}
growth={'website':1.0,'referral':1.0,'ria':1.0,'broker':1.0,'platform':1.0}
types=['Individual']*7+['Trust']*2+['Family office']
states=['NY','NY','CA','FL','TX','CT','NJ','IL','MA','WA','CO','GA']
reasons=['Rebalancing','Performance drawdown','Liquidity need','Adviser moved client','Estate or other']
inv=[];ev=[];eid=0
def E(i,d,e,detail=''):
    global eid; eid+=1; ev.append(dict(event_id=f"E{eid:05d}",investor_id=i,date=d.isoformat(),event=e,detail=detail))
nid=10000
firms={k:[f"{CH[k][4]}-{n:03d}" for n in random.sample(range(1,200),12)] for k in CH if CH[k][4]}
def rday(m): return m+dt.timedelta(days=random.randint(0,27))
for ch,(lab,ann,tick,ser,pre) in CH.items():
    for m in months:
        # ramp: platform launched growth over time; website grows after platform launch 2025
        mult=1.0
        if ch=='website': mult=0.5 if m<dt.date(2025,1,1) else (0.9 if m<dt.date(2025,10,1) else 1.35)
        if ch=='platform': mult=0.3 if m<dt.date(2025,1,1) else 1.1
        if ch=='ria': mult=0.8 if m<dt.date(2025,10,1) else 1.15
        if ch=='broker': mult=1.1 if m<dt.date(2025,10,1) else 0.9
        lam=ann/12*mult
        n=sum(1 for _ in range(40) if random.random()<lam/40)
        for _ in range(n):
            nid+=1; iid=f"INV-{nid}"
            funded=rday(m)
            if funded>ASOF: funded=ASOF
            dtf=int(random.lognormvariate(math.log({'website':48,'referral':30,'ria':38,'broker':26,'platform':22}[ch]),0.45))
            first=funded-dt.timedelta(days=dtf)
            amt=round(random.lognormvariate(math.log(tick),0.6)/5000)*5000; amt=max(amt,25000)
            firm=random.choice(firms[ch]) if pre else ''
            t=random.choice(types); tier='QEP' if (t=='Family office' or amt>=1000000) else 'Accredited'
            if ch=='website': E(iid,first,'First website visit','Insights article')
            if ch=='website': E(iid,first+dt.timedelta(days=dtf//6),'Used portfolio-fit tool','')
            reg=first+dt.timedelta(days=dtf//4) if ch=='website' else first
            E(iid,reg,'Registered', 'Via '+firm if firm else ('Website sign-up' if ch=='website' else 'Introduced by existing client'))
            ver=reg+dt.timedelta(days=max(1,dtf//5)); E(iid,ver,'Eligibility verified',tier)
            ql=ver+dt.timedelta(days=max(1,dtf//6)); E(iid,ql,'IR meeting' if not pre else 'Proposal sent','')
            ss=funded-dt.timedelta(days=max(2,dtf//5)); E(iid,ss,'Subscription started',f'Series {ser}')
            E(iid,funded,'Funded',f'${amt:,.0f}')
            # life after funding
            val=amt; tops=[]; red=None; reqd=None; reason=''
            cur=addm(mstart(funded.year,funded.month),1)
            hazard={'website':0.010,'referral':0.006,'ria':0.009,'broker':0.014,'platform':0.012}[ch]
            dd=0; peak=0
            while cur<=mstart(ASOF.year,ASOF.month):
                val*=1+ret[cur]
                h=hazard*(2.2 if ret[cur]<-0.03 else 1)
                if random.random()<0.02:
                    ta=round(amt*random.uniform(0.2,0.6)/5000)*5000; val+=ta; tops.append((rday(cur),ta)); E(iid,tops[-1][0],'Top-up',f'${ta:,.0f}')
                if random.random()<h:
                    reqd=rday(cur); reason=random.choices(reasons,[3,4,2,1 if pre else 0.2,1])[0]
                    E(iid,reqd,'Redemption requested',reason)
                    rd=addm(cur,1)+dt.timedelta(days=-1)+dt.timedelta(days=0)
                    rdate=dt.date(rd.year,rd.month,1)+dt.timedelta(days=27)
                    if rdate<=ASOF:
                        red=(rdate,round(val)); E(iid,rdate,'Fully redeemed',f'${round(val):,.0f}')
                    break
                cur=addm(cur,1)
            status='Redeemed' if red else ('Redemption requested' if reqd else 'Active')
            risk=''
            if status=='Active':
                if random.random()<0.08: risk=random.choice(['Frequent logins during drawdown','No contact in 9+ months','Adviser changed firms' if pre else 'Asked about liquidity terms'])
            inv.append(dict(investor_id=iid,channel=ch,channel_label=lab,introduced_by=firm,investor_type=t,tier=tier,state=random.choice(states),
                series=ser,first_touch=first.isoformat(),funded=funded.isoformat(),days_to_fund=dtf,initial_usd=amt,
                topups_usd=sum(a for _,a in tops),current_value_usd=0 if red else round(val),redeemed_usd=red[1] if red else 0,
                redemption_requested=reqd.isoformat() if reqd else '',redeemed=red[0].isoformat() if red else '',redemption_reason=reason,status=status,risk_flag=risk))
            invtmp=inv[-1]; invtmp['_tops']=tops
# pipeline (not yet funded)
for ch,(lab,ann,tick,ser,pre) in CH.items():
    for _ in range(int(ann*0.9)):
        nid+=1; iid=f"INV-{nid}"; firm=random.choice(firms[ch]) if pre else ''
        first=ASOF-dt.timedelta(days=random.randint(5,120)); stage=random.choice(['Registered','Eligibility verified','Eligibility verified','IR meeting' if not pre else 'Proposal sent','Subscription started'])
        steps=(['First website visit'] if ch=='website' else [])+['Registered','Eligibility verified','IR meeting' if not pre else 'Proposal sent','Subscription started']
        d=first
        for s in steps:
            E(iid,d,s,'Via '+firm if (s=='Registered' and firm) else '')
            if s==stage: break
            d=d+dt.timedelta(days=random.randint(2,12))
            if d>ASOF: d=ASOF
        t=random.choice(types)
        st={'Registered':'Registered','Eligibility verified':'Verified','Subscription started':'Onboarding'}.get(stage,'Qualified lead')
        inv.append(dict(investor_id=iid,channel=ch,channel_label=lab,introduced_by=firm,investor_type=t,tier='' if st=='Registered' else 'Accredited',state=random.choice(states),
            series='',first_touch=first.isoformat(),funded='',days_to_fund='',initial_usd=0,topups_usd=0,current_value_usd=0,redeemed_usd=0,
            redemption_requested='',redeemed='',redemption_reason='',status=st,risk_flag='',_tops=[]))
# monthly flows Oct24..Sep26 per channel
win=[addm(dt.date(2024,10,1),i) for i in range(24)]
def ym(s): return s[:7]
flows=[]
for ch in CH:
    for m in win:
        k=m.strftime('%Y-%m')
        rows=[i for i in inv if i['channel']==ch]
        new=[i for i in rows if i['funded'] and ym(i['funded'])==k]
        subs=sum(i['initial_usd'] for i in new)
        tops=sum(a for i in rows for d,a in i['_tops'] if d.strftime('%Y-%m')==k)
        reds=[i for i in rows if i['redeemed'] and ym(i['redeemed'])==k]
        reqs=[i for i in rows if i['redemption_requested'] and ym(i['redemption_requested'])==k]
        flows.append(dict(month=k,channel=ch,new_investors=len(new),subscriptions_usd=subs,topups_usd=tops,
            redemptions_usd=sum(i['redeemed_usd'] for i in reds),redemption_requests=len(reqs),full_redemptions=len(reds),
            topup_count=sum(1 for i in rows for d,a in i['_tops'] if d.strftime('%Y-%m')==k)))
# active & aum end of month: simulate per investor
for f in flows:
    me=addm(dt.date(int(f['month'][:4]),int(f['month'][5:]),1),1)-dt.timedelta(days=1)
    act=0;aum=0.0
    for i in inv:
        if i['channel']!=f['channel'] or not i['funded']: continue
        fd=dt.date.fromisoformat(i['funded'])
        if fd>me: continue
        if i['redeemed'] and dt.date.fromisoformat(i['redeemed'])<=me: continue
        act+=1
        v=i['initial_usd']; cur=addm(mstart(fd.year,fd.month),1)
        while cur<=mstart(me.year,me.month):
            v*=1+ret[cur]
            v+=sum(a for d,a in i['_tops'] if d.year==cur.year and d.month==cur.month)
            cur=addm(cur,1)
        aum+=v
    f['active_investors']=act; f['aum_usd']=round(aum)
# funnel monthly
stages=['Website visitors','Engaged visitors','Registered','Eligibility verified','Qualified lead','Subscription started','Funded']
fun=[]
for f in flows:
    ch=f['channel']; k=f['month']
    funded=f['new_investors']
    sub=funded+random.randint(0,2)
    ql=round(sub/random.uniform(0.40,0.55)) if ch in('website','referral') else round(sub/random.uniform(0.6,0.75))
    ver=round(ql/random.uniform(0.40,0.55)) if ch=='website' else round(ql/random.uniform(0.65,0.85))
    reg=round(ver/random.uniform(0.28,0.38)) if ch=='website' else round(ver/random.uniform(0.75,0.9))
    if ch=='website':
        mm=dt.date(int(k[:4]),int(k[5:]),1)
        vis=int(random.uniform(5200,6400)*(1.0 if mm<dt.date(2025,10,1) else 1.3))
        eng=round(vis*random.uniform(0.07,0.10)); reg=max(reg,round(eng*random.uniform(0.10,0.14)))
    else: vis=0;eng=0
    for o,(s,c) in enumerate(zip(stages,[vis,eng,reg,ver,ql,sub,funded])):
        fun.append(dict(month=k,channel=ch,stage_order=o+1,stage=s,count=c))
for i in inv: i.pop('_tops')
import os
os.makedirs('data',exist_ok=True)
def wcsv(name,rows):
    with open(name,'w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
wcsv('data/sample_investors.csv',inv); wcsv('data/sample_events.csv',sorted(ev,key=lambda e:(e['investor_id'],e['date'])))
wcsv('data/sample_flows.csv',flows); wcsv('data/sample_funnel.csv',fun)
print(len(inv),len(ev),len(flows),len(fun))
fl=[f for f in flows if f['month']>='2025-10']
print('funded last12',sum(f['new_investors'] for f in fl),'subs',sum(f['subscriptions_usd'] for f in fl),'red',sum(f['redemptions_usd'] for f in fl))
print('aum end',sum(f['aum_usd'] for f in flows if f['month']=='2026-09'),'active',sum(f['active_investors'] for f in flows if f['month']=='2026-09'))
for ch in CH: print(ch,sum(f['new_investors'] for f in fl if f['channel']==ch), sum(f['count'] for f in fun if f['channel']==ch and f['month']>='2025-10' and f['stage_order']==3))
