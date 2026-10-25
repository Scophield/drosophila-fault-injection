"""Render record-linked 2-D research animations without running a neural model.

All drawing uses Python/Pillow. FFmpeg encodes those frames and edits the three
completed clips into the overview. No approximate plant dynamics are introduced.
"""
from pathlib import Path
import argparse
import bisect
import csv
import hashlib
import json
import math
import platform
import subprocess
import time

from PIL import Image, ImageDraw, ImageFont
import PIL
from matplotlib.font_manager import FontProperties, findfont

W, H, SCALE, FPS = 1280, 720, 2, 24
BG, WHITE, INK, MUTED = "#F1F5F7", "#FFFFFF", "#193549", "#5E7381"
LINE, GRID = "#D2DEE4", "#EAF0F3"
AGENT, THREAT, SIGNAL, BURST = "#087F8C", "#C74D49", "#7551B0", "#D49528"
COMMIT = "75313d7740491e7f7830e2fc554c21e1aaefe655"
NAMES = {"A": "demo-a-delay", "B": "demo-b-control", "C": "demo-c-horizon"}
FONT_FILES = {False: findfont(FontProperties(family="DejaVu Sans")),
              True: findfont(FontProperties(family="DejaVu Sans", weight="bold"))}
FONTS = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font(size, bold=False):
    key = size, bold
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(FONT_FILES[bold], round(size*SCALE))
    return FONTS[key]


class Canvas:
    def __init__(self):
        self.image = Image.new("RGB", (W*SCALE, H*SCALE), BG)
        self.d = ImageDraw.Draw(self.image)

    def text(self, xy, text, size=18, color=INK, bold=False, anchor="la"):
        self.d.text(tuple(v*SCALE for v in xy), str(text), font=font(size, bold),
                    fill=color, anchor=anchor)

    def rect(self, bbox, fill=WHITE, outline=None, radius=0, width=1):
        box = tuple(round(v*SCALE) for v in bbox)
        if radius:
            self.d.rounded_rectangle(box, radius=round(radius*SCALE), fill=fill,
                                     outline=outline, width=round(width*SCALE))
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=round(width*SCALE))

    def line(self, pts, color=LINE, width=1):
        if len(pts) > 1:
            self.d.line([(round(x*SCALE), round(y*SCALE)) for x,y in pts],
                        fill=color, width=max(1, round(width*SCALE)), joint="curve")

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.d.ellipse(tuple(round(v*SCALE) for v in box), fill=fill,
                       outline=outline, width=round(width*SCALE))

    def polygon(self, pts, fill, outline=None, width=1):
        self.d.polygon([(round(x*SCALE), round(y*SCALE)) for x,y in pts],
                       fill=fill, outline=outline, width=round(width*SCALE))

    def finish(self):
        return self.image.resize((W,H), Image.Resampling.LANCZOS)


def lerp(a, b, f):
    return [a[j]+f*(b[j]-a[j]) for j in range(2)]


class Record:
    def __init__(self, obj):
        self.r = obj
        self.segments = obj["segments"]
        self.starts = [s["t0"] for s in self.segments]
        self.times, self.rates = obj["command_times_ms"], obj["command_hz"]
        self.contact = obj["contact_ms"]
        self.trigger, self.onset, self.end = obj["trigger_ms"], obj["onset_ms"], obj["B_ms"]

    def state(self, t):
        shown = min(t, self.contact) if self.contact is not None else t
        i = min(len(self.segments)-1, max(0, bisect.bisect_right(self.starts, shown)-1))
        s = self.segments[i]
        f = min(1., max(0., (shown-s["t0"])/(s["t1"]-s["t0"])))
        a, b = lerp(s["fly0"],s["fly1"],f), lerp(s["target0"],s["target1"],f)
        h = s["heading1"] if shown >= s["t1"]-1e-9 else s["heading0"]
        return dict(t=shown, fly=a, target=b, heading=h,
                    contact=self.contact is not None and t>=self.contact-1e-8,
                    separation=math.dist(a,b))

    def path(self, t, who):
        shown = self.state(t)
        pts = [self.segments[0][who+"0"]]
        pts += [s[who+"1"] for s in self.segments if s["t1"] <= shown["t"]+1e-10]
        pts += [shown["fly" if who=="fly" else "target"]]
        return pts

    def rate(self, t):
        t = self.state(t)["t"]
        return self.rates[max(0,bisect.bisect_right(self.times,t+1e-10)-1)]


def mapped(wall, knots):
    for (w0,t0),(w1,t1) in zip(knots[:-1],knots[1:]):
        if wall <= w1+1e-10:
            f = min(1.,max(0.,(wall-w0)/(w1-w0)))
            return t0+f*(t1-t0), (t1-t0)/(w1-w0)/1000
    return knots[-1][1], 0.


def dashed(c, pts, color, width=2, dash=6, gap=5):
    distance_walked=0.
    for (a,b) in zip(pts[:-1],pts[1:]):
        d=math.dist(a,b)
        if d<.01: continue
        u=((b[0]-a[0])/d,(b[1]-a[1])/d)
        k=0.
        while k<d:
            phase=(distance_walked+k)%(dash+gap)
            on=phase<dash
            remaining=(dash if on else dash+gap)-phase
            q=min(d,k+max(1e-7,remaining))
            if on:c.line([(a[0]+u[0]*k,a[1]+u[1]*k),(a[0]+u[0]*q,a[1]+u[1]*q)],color,width)
            k=q
        distance_walked+=d


def fly_icon(c, x, y, heading):
    ang=math.radians(heading)
    def point(a,b):
        return (x+a*math.cos(ang)+b*math.sin(ang),y-a*math.sin(ang)+b*math.cos(ang))
    # Static illustration; no wing motion or biological size interpretation.
    c.polygon([point(-5,-3),point(-13,-12),point(-1,-9),point(4,-2)], "#B9DAD9", AGENT)
    c.polygon([point(-5,3),point(-13,12),point(-1,9),point(4,2)], "#B9DAD9", AGENT)
    for a in [-5,0,5]:
        c.line([point(a,-3),point(a-4,-8)],AGENT,1.3)
        c.line([point(a,3),point(a-4,8)],AGENT,1.3)
    c.line([point(-9,0),point(8,0)],AGENT,6)
    xx,yy=point(9,0);c.ellipse((xx-3.6,yy-3.6,xx+3.6,yy+3.6),AGENT)
    c.line([point(12,0),point(30,0)],AGENT,2)
    c.polygon([point(31,0),point(25,-3.5),point(25,3.5)],AGENT)


class Renderer:
    def __init__(self, examples, data_root=None):
        self.path=examples
        self.e=json.loads(examples.read_text())
        assert self.e["source_commit"]==COMMIT
        self.records={}
        for group in "ABC":
            for q in self.e[group]["records"]:
                p=examples.parent/q["replay_file"]
                assert sha(p)==q["replay_sha256"]
                if data_root is not None:
                    assert sha(data_root/q["source"])==q["source_sha256"]
                self.records[q["id"]]=Record(json.loads(p.read_text()))
        self.groups={key:[self.records[q["id"]] for q in self.e[key]["records"]] for key in "ABC"}
        if data_root:
            assert subprocess.check_output(["git","rev-parse","HEAD"],cwd=data_root,text=True).strip()==COMMIT
        assert all(self.e["B"][key] for key in ["same_mask","same_uniforms","same_input_map","same_calibration","same_schedule","pretrigger_prefix_identical"])
        b=self.groups["B"][0]
        assert 900<b.contact<1000 and self.groups["C"][0].r["id"]==b.r["id"]
        self.knots={"A":[(0,0),(1.2,0),(5.5,max(r.trigger for r in self.groups["A"])),(6.3,max(r.trigger for r in self.groups["A"])),(14.2,1000),(17,1000)],
                    "B":[(0,0),(1.2,0),(4.8,b.trigger),(5.6,b.trigger),(13.2,b.contact),(14.2,b.contact),(16,1000),(17,1000)],
                    "C":[(0,0),(1.2,0),(9.4,900),(11.2,900),(14.6,b.contact),(15.6,b.contact),(17,1000),(18,1000)]}
        self.duration={"A":17.,"B":17.,"C":18.}
        self.poster_wall={"A":6.,"B":13.8,"C":10.2}
        points=[]
        for r in self.records.values():
            for s in r.segments:
                if r.contact is not None and s["t0"]>r.contact:break
                for p in [s["fly0"],r.state(min(s["t1"],r.contact or 1000))["fly"]]:
                    points.extend([(p[0]-.06,p[1]-.06),(p[0]+.06,p[1]+.06)])
                points.append(s["target0"])
        self.bounds=(math.floor(min(p[0] for p in points)/.05)*.05,
                     math.ceil(max(p[0] for p in points)/.05)*.05,
                     math.floor(min(p[1] for p in points)/.05)*.05,
                     math.ceil(max(p[1] for p in points)/.05)*.05)
        self.signalmax=max(8.,math.ceil(max(v for r in self.groups["A"] for t,v in zip(r.times,r.rates) if r.contact is None or t<=r.contact)/5)*5)

    def header(self,c,key,t,speed):
        titles={"A":"A  |  Connection loss changes action timing", "B":"B  |  Same schedule, different trajectories", "C":"C  |  Keep watching the same trajectory"}
        c.rect((0,0,W,121),WHITE)
        c.text((32,12),"FLY-CONNECTOME SNN  /  FROZEN V10.1 RECORDS",14,MUTED,bold=True)
        c.text((32,35),titles[key],29,INK,True)
        r=self.groups[key][0].r
        subtitle=f"Illustrative example  •  {r['RF']}  •  seed {r['seed']}  •  bearing {r['bearing_deg']:+.0f}°"
        subtitle += "  •  proportional (P)" if key=="A" else "  •  50% connection-row deletion"
        c.text((32,82),subtitle,18,MUTED)
        c.text((1248,14),"SIMULATION TIME",14,MUTED,True,anchor="ra")
        c.text((1248,36),f"{t:08.3f} ms / 1000 ms",22,INK,True,anchor="ra")
        c.text((1248,81),"Playback: PAUSED" if speed==0 else f"Playback: {speed:.3f}×",17,MUTED,anchor="ra")

    def scene(self,c,r,t,viewport):
        x,y,w,h=viewport;x0,x1,y0,y1=self.bounds
        scale=min(w/(x1-x0),h/(y1-y0));ww=(x1-x0)*scale;hh=(y1-y0)*scale
        left=x+(w-ww)/2;top=y+(h-hh)/2
        def xy(p):return left+(p[0]-x0)*scale,top+(y1-p[1])*scale
        for j in range(math.ceil(x0/.05),math.floor(x1/.05)+1):
            xx=j*.05;c.line([xy((xx,y0)),xy((xx,y1))],GRID,1)
            if j%2==0:c.text((xy((xx,y0))[0],top+hh+3),f"{xx*1000:.0f}",13,MUTED,anchor="ma")
        for j in range(math.ceil(y0/.05),math.floor(y1/.05)+1):
            yy=j*.05;c.line([xy((x0,yy)),xy((x1,yy))],GRID,1)
            if j%2==0:c.text((left-5,xy((x0,yy))[1]),f"{yy*1000:.0f}",13,MUTED,anchor="rm")
        c.line([xy((x0,y0)),xy((x1,y0))],LINE,1.2)
        c.text((left+ww,top+hh+21),"x (mm)",13,MUTED,anchor="ra")
        c.text((left-1,top-19),"y (mm)",13,MUTED)
        state=r.state(t);a,b=xy(state["fly"]),xy(state["target"])
        c.line([xy(p) for p in r.path(t,"fly")],AGENT,2.8)
        dashed(c,[xy(p) for p in r.path(t,"target")],THREAT,1.7,5,4)
        radius=.05*scale
        c.ellipse((a[0]-radius,a[1]-radius,a[0]+radius,a[1]+radius),outline=THREAT if state["contact"] else "#90B6BD",width=2)
        # A real 50-mm boundary, separate from the static decorative icons.
        fly_icon(c,*a,state["heading"])
        c.polygon([(b[0],b[1]-8),(b[0]+8,b[1]),(b[0],b[1]+8),(b[0]-8,b[1])],THREAT,WHITE,1)
        if state["contact"]:
            c.line([a,b],THREAT,2)
            c.ellipse((b[0]-11,b[1]-11,b[0]+11,b[1]+11),outline=THREAT,width=2)
        return state

    def phase(self,r,t):
        if r.state(t)["contact"]:return "Contact latched"
        if t<r.trigger:return "Waiting for neural trigger"
        if t<r.onset:return "Triggered; burst pending"
        if t<r.end:return "Burst active"
        return "Walking after burst"

    def timeline(self,c,r,t,x,y,w,labels=True):
        xx=lambda z:x+w*z/1000
        c.line([(x,y),(x+w,y)],LINE,3)
        c.line([(xx(r.onset),y),(xx(r.end),y)],"#E7BF75",8)
        for at,symbol in [(r.trigger,"T"),(r.onset,"A"),(r.end,"E")]:
            pos=xx(at);color=INK if t>=at else MUTED
            if symbol=="T":c.ellipse((pos-5,y-5,pos+5,y+5),SIGNAL if t>=at else WHITE,SIGNAL,2)
            elif symbol=="A":c.polygon([(pos,y-7),(pos-6,y+5),(pos+6,y+5)],BURST)
            else:c.rect((pos-4,y-5,pos+4,y+5),BURST)
            if labels:c.text((pos,y+11),f"{symbol} {at:.0f}",14,color,anchor="ma")
        c.line([(xx(t),y-9),(xx(t),y+8)],INK,2)

    def signal(self,c,r,t,box):
        x,y,w,h=box;xx=lambda v:x+w*v/1000;yy=lambda v:y+h*(1-v/self.signalmax)
        c.line([(x,y+h),(x+w,y+h)],LINE,1)
        dashed(c,[(x,yy(r.r["theta"])),(x+w,yy(r.r["theta"]))],SIGNAL,1,4,3)
        limit=r.state(t)["t"];pts=[];last=r.rates[0]
        for at,v in zip(r.times,r.rates):
            if at>limit+1e-10:break
            if pts:pts.append((xx(at),yy(last)))
            pts.append((xx(at),yy(v)));last=v
        if pts:pts.append((xx(limit),yy(last)))
        c.line(pts,SIGNAL,2)
        c.line([(xx(t),y-2),(xx(t),y+h+2)],INK,1)
        c.text((x,y-21),f"Mean command {r.rate(t):.2f} Hz  /  θ {r.r['theta']:.2f}",14,SIGNAL)
        c.text((x,y+h+4),"0",13,MUTED);c.text((x+w,y+h+4),"1000 ms",13,MUTED,anchor="ra")

    def footer(self,c,key,t):
        c.rect((0,649,W,H),WHITE)
        if key=="A":message="Matched seed and controller; neural triggers and actuator times are distinct."
        elif key=="B":message="Same damage and event schedule; complete feedback configurations produce different contact outcomes."
        elif t<900:message="One recorded trajectory, scored at 900 ms and at 1000 ms."
        elif t<self.groups['C'][0].contact:message="Contact-free at 900 ms. Keep watching the same recorded trajectory."
        else:message="Same trajectory, different endpoints: contact-free at 900 ms; contact recorded by 1000 ms."
        c.text((32,657),message,19,INK,True)
        if key=="A":c.text((32,687),"T: neural trigger  |  A: burst starts  |  E: burst ends  •  Teal: agent  •  Coral: pursuer  •  Ring: 50 mm  •  Icons not to scale",14,MUTED)
        else:c.text((32,687),"Teal: agent  •  Coral: pursuer  •  Ring: 50 mm center-distance boundary  •  Static icons are not to scale",15,MUTED)

    def frame(self,key,wall,with_audit=False):
        t,speed=mapped(wall,self.knots[key]);c=Canvas();self.header(c,key,t,speed);states=[]
        if key=="A":
            width=(1216-32)/3
            for j,r in enumerate(self.groups[key]):
                x=32+j*(width+16);c.rect((x,133,x+width,638),WHITE,LINE,12)
                c.text((x+18,145),r.r["condition_label"],24,INK,True)
                c.text((x+18,177),self.phase(r,t),16,THREAT if r.state(t)["contact"] else MUTED)
                state=self.scene(c,r,t,(x+22,215,width-42,246));states.append((r,state))
                c.text((x+18,490),f"Heading {state['heading']:+.1f}°",16,AGENT)
                self.timeline(c,r,t,x+24,524,width-48)
                self.signal(c,r,t,(x+24,587,width-48,24))
        elif key=="B":
            for j,r in enumerate(self.groups[key]):
                x=32+j*616;c.rect((x,133,x+600,553),WHITE,LINE,12)
                c.text((x+20,146),r.r["control_label"],24,INK,True)
                st=r.state(t)
                if st["contact"]:status=f"First contact {r.contact:.3f} ms"
                elif t>=1000:status="Contact-free through 1000 ms"
                else:status="Contact-free so far"
                c.text((x+20,179),status,19,THREAT if st["contact"] else AGENT,True)
                states.append((r,self.scene(c,r,t,(x+44,222,514,270))))
                c.text((x+20,523),f"Heading {st['heading']:+.1f}°  •  {self.phase(r,t)}",17,MUTED)
            r=self.groups[key][0]
            c.text((42,568),"SHARED RECORDED SCHEDULE",16,INK,True)
            c.text((1240,567),"T: neural trigger  |  A: actuator starts  |  E: burst ends",15,MUTED,anchor="ra")
            self.timeline(c,r,t,64,602,1152)
            if t>=r.contact:c.text((640,625),"P held at exact first-contact pose; R continues to the stated endpoint.",15,MUTED,anchor="ma")
        else:
            r=self.groups[key][0];c.rect((32,133,632,553),WHITE,LINE,12);c.rect((648,133,1248,553),WHITE,LINE,12)
            c.text((52,146),r.r["control_label"],24,INK,True)
            c.text((52,179),self.phase(r,t),18,THREAT if r.state(t)["contact"] else AGENT,True)
            states.append((r,self.scene(c,r,t,(76,221,514,270))))
            c.text((52,523),"Pose freezes at first contact; simulated clock continues.",16,MUTED)
            c.text((674,154),"ONE TRACE, TWO ENDPOINTS",17,INK,True)
            for y,label,value,active,color in [
                (205,"900 ms checkpoint","Contact-free at 900 ms",t>=900,AGENT),
                (316,"First geometric contact",f"{r.contact:.3f} ms",t>=r.contact,THREAT),
                (427,"1000 ms endpoint","Contact recorded",t>=1000,THREAT)]:
                c.text((674,y),label,18,MUTED)
                c.text((674,y+31),value if active else "Pending observation",26,color if active else "#91A0AA",True)
            c.text((42,567),"LATE WINDOW  /  SAME TRAJECTORY",16,INK,True)
            x,w,y=64,1152,607
            c.line([(x,y),(x+w,y)],LINE,4)
            for v,label in [(900,"900 ms"),(r.contact,f"First contact {r.contact:.3f} ms"),(1000,"1000 ms")]:
                if v==r.contact and t<r.contact:continue
                pos=x+w*(v-900)/100;c.line([(pos,y-7),(pos,y+7)],THREAT if v==r.contact else INK,2)
                c.text((pos,y+11),label,15,MUTED,anchor="ma")
            if t>=900:
                pos=x+w*(min(1000,t)-900)/100;c.ellipse((pos-6,y-6,pos+6,y+6),INK)
            c.text((1240,568),"Burst ends at 900 ms in this record",15,MUTED,anchor="ra")
        self.footer(c,key,t)
        audit=[]
        if with_audit:
            for r,s in states:
                audit.append(dict(wall_s=wall,simulation_ms=t,playback_factor=speed,record_id=r.r["id"],
                                  display_ms=s["t"],fly_x_m=s["fly"][0],fly_y_m=s["fly"][1],
                                  pursuer_x_m=s["target"][0],pursuer_y_m=s["target"][1],
                                  heading_deg=s["heading"],separation_m=s["separation"],contact_latched=s["contact"]))
        return c.finish(),audit


def encode_clip(renderer,key,target,ffmpeg,qa):
    duration=renderer.duration[key];count=round(duration*FPS);audit=[]
    cmd=[str(ffmpeg),"-hide_banner","-loglevel","warning","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0","-an","-c:v","libx264",
         "-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-threads","2",
         "-movflags","+faststart",str(target)]
    with (qa/(target.stem+"-encode.log")).open("wb") as log:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        try:
            for i in range(count):
                frame,rows=renderer.frame(key,i/FPS,True)
                process.stdin.write(frame.tobytes())
                audit.extend(dict(frame=i,**r) for r in rows)
                if i%120==0:print(f"{key}: {i}/{count} frames",flush=True)
        finally:
            process.stdin.close()
        assert process.wait()==0, target
    with (qa/(target.stem+"-frame-data.csv")).open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(audit[0]));writer.writeheader();writer.writerows(audit)
    return dict(duration_s=duration,frames=count,fps=FPS,width=W,height=H,codec="H.264",pixel_format="yuv420p",audio=False,
                simulation_knots=renderer.knots[key],condition_ids=[r.r["id"] for r in renderer.groups[key]])


def run(cmd):
    p=subprocess.run(list(map(str,cmd)),capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors="replace")[-3000:])


def gif(ffmpeg,source,target):
    for width,fps,colors in [(800,8,112),(720,6,96)]:
        filt=f"[0:v]fps={fps},scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4"
        run([ffmpeg,"-hide_banner","-loglevel","error","-y","-i",source,"-filter_complex",filt,"-loop","0",target])
        if target.stat().st_size<5_000_000:break
    return dict(width=width,fps=fps,colors=colors,bytes=target.stat().st_size,loop=0)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--examples",type=Path,default=Path("docs/homepage-animation/examples.json"))
    ap.add_argument("--data-root",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--ffmpeg",type=Path)
    ap.add_argument("--posters-only",action="store_true")
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);qa=a.out/"qa";qa.mkdir()
    renderer=Renderer(a.examples,a.data_root)
    manifest=dict(scientific_commit=COMMIT,example_manifest_sha256=sha(a.examples),renderer_sha256=sha(__file__),
                  runtime=dict(python=platform.python_version(),pillow=PIL.__version__),
                  coordinate_bounds_m=renderer.bounds,illustrative_examples=True,neural_simulation=False,clips={})
    for key,name in NAMES.items():
        image,_=renderer.frame(key,renderer.poster_wall[key]);image.save(a.out/(name+".png"))
    if a.posters_only:
        (a.out/"poster-check.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print("Posters created from verified record segments.");return
    assert a.ffmpeg and a.ffmpeg.is_file(),"Provide an existing FFmpeg executable"
    manifest["encoder_sha256"]=sha(a.ffmpeg)
    for key,name in NAMES.items():
        path=a.out/(name+".mp4")
        manifest["clips"][name]=encode_clip(renderer,key,path,a.ffmpeg,qa)
        manifest["clips"][name]["gif"]=gif(a.ffmpeg,path,a.out/(name+".gif"))
    trims=[("A",3.,12.),("B",8.,17.),("C",10.,18.)]
    inputs=[]
    for key,_,_ in trims:inputs += ["-i",str(a.out/(NAMES[key]+".mp4"))]
    filters=[f"[{i}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]" for i,(_,start,end) in enumerate(trims)]
    filters.append("[v0][v1][v2]concat=n=3:v=1:a=0[out]")
    run([a.ffmpeg,"-hide_banner","-loglevel","error",*inputs,"-filter_complex",";".join(filters),"-map","[out]",
         "-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-threads","2",
         "-r",str(FPS),"-fps_mode","cfr","-movflags","+faststart",a.out/"overview.mp4"])
    run([a.ffmpeg,"-hide_banner","-loglevel","error","-i",a.out/"overview.mp4","-ss","14.8","-frames:v","1",a.out/"overview.png"])
    manifest["clips"]["overview"]=dict(duration_s=26.,frames=26*FPS,fps=FPS,width=W,height=H,
        source_edits=[dict(clip=NAMES[k],start_wall_s=s,end_wall_s=e) for k,s,e in trims],
        no_new_experiment=True,gif=gif(a.ffmpeg,a.out/"overview.mp4",a.out/"overview.gif"))
    for path in a.out.glob("*.*"):
        if path.suffix in [".mp4",".gif",".png"]:
            manifest.setdefault("files",{})[path.name]=dict(bytes=path.stat().st_size,sha256=sha(path))
    (a.out/"render-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"created":list(manifest["files"]),"durations_s":{k:v["duration_s"] for k,v in manifest["clips"].items()}},indent=2))


if __name__=="__main__":main()
