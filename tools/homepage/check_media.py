"""Decode and audit the actual encoded homepage media (no scientific simulation)."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont
from matplotlib.font_manager import findfont, FontProperties


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(cmd):
    p = subprocess.run(list(map(str, cmd)), capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace")[-3000:])
    return p


def sheet(frames, output):
    font = ImageFont.truetype(findfont(FontProperties(family="DejaVu Sans")), 19)
    canvas = Image.new("RGB", (1280, 390*((len(frames)+1)//2)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (path, label) in enumerate(frames):
        x, y = (i % 2)*640, (i//2)*390
        with Image.open(path) as im:
            canvas.paste(im.convert("RGB").resize((640,360), Image.Resampling.LANCZOS), (x,y+30))
        draw.text((x+10,y+5), label, font=font, fill="#193549")
    canvas.save(output)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--media", type=Path, required=True)
    ap.add_argument("--ffmpeg", type=Path, required=True)
    a = ap.parse_args()
    manifest = json.loads((a.media/"render-manifest.json").read_text())
    qa = a.media/"qa"
    qa.mkdir(exist_ok=True)
    report = dict(scientific_commit=manifest["scientific_commit"], clips={},
                  github_remote_rendering="Not verified: local unpublished candidate")
    times = {
        "demo-a-delay": [0.,6.,12.,16.9],
        "demo-b-control": [0.,8.,13.8,16.9],
        "demo-c-horizon": [0.,10.2,15.1,17.9],
        "overview": [0.,8.9,14.8,25.9],
    }
    for name, spec in manifest["clips"].items():
        path = a.media/(name+".mp4")
        probe = subprocess.run([str(a.ffmpeg),"-hide_banner","-i",str(path)],capture_output=True)
        metadata = probe.stderr.decode(errors="replace")
        (qa/(name+"-metadata.txt")).write_text(metadata,encoding="utf-8")
        duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)",metadata)
        assert duration, metadata
        seconds = int(duration[1])*3600+int(duration[2])*60+float(duration[3])
        assert abs(seconds-spec["duration_s"]) < .02
        assert "h264" in metadata and "1280x720" in metadata and "yuv420p" in metadata
        assert "24 fps" in metadata and "Audio:" not in metadata
        decoded = run([a.ffmpeg,"-hide_banner","-v","error","-i",path,
                       "-map","0:v:0","-an","-progress","pipe:1","-f","null","-"])
        progress = decoded.stdout.decode(errors="replace")
        counts = re.findall(r"^frame=(\d+)$",progress,re.MULTILINE)
        assert counts and int(counts[-1]) == spec["frames"], progress
        assert not decoded.stderr.strip(), decoded.stderr
        frames = []
        for i,t in enumerate(times[name]):
            out = qa/f"{name}-decoded-{i}.png"
            run([a.ffmpeg,"-hide_banner","-loglevel","error","-y","-ss",t,
                 "-i",path,"-frames:v","1",out])
            frames.append((out,f"{name} / video {t:.1f} s"))
        sheet(frames,qa/(name+"-decoded-sheet.png"))
        with Image.open(a.media/(name+".gif")) as gif:
            info = dict(width=gif.width,height=gif.height,frames=gif.n_frames,
                        loop=gif.info.get("loop"),bytes=(a.media/(name+".gif")).stat().st_size)
            duration_ms = 0
            for j in range(gif.n_frames):
                gif.seek(j)
                duration_ms += gif.info.get("duration",0)
                gif.load()
            info["duration_s"] = duration_ms/1000
            assert info["loop"] == 0 and info["width"] == spec["gif"]["width"]
            assert info["bytes"] < 5_000_000
            assert abs(info["duration_s"]-spec["duration_s"]) < .15
            gf = []
            for j in [0,gif.n_frames//2,gif.n_frames-1]:
                gif.seek(j)
                out = qa/f"{name}-gif-{j}.png"
                gif.convert("RGB").save(out)
                gf.append((out,f"{name} GIF / frame {j}"))
            sheet(gf,qa/(name+"-gif-sheet.png"))
        if name != "overview":
            rows = list(csv.DictReader((qa/(name+"-frame-data.csv")).open(newline="")))
            assert len(rows) == spec["frames"]*len(spec["condition_ids"])
            by_frame = {}
            for row in rows:
                by_frame.setdefault(int(row["frame"]),[]).append(row)
                assert float(row["display_ms"]) <= float(row["simulation_ms"])+1e-8
                if row["contact_latched"] == "True":
                    assert abs(float(row["separation_m"])-.05)<1e-8
            assert all(len({r["simulation_ms"] for r in group}) == 1 for group in by_frame.values())
            # The endpoint must actually occur in encoded frames, not merely at t=duration.
            assert {float(r["simulation_ms"]) for r in by_frame[max(by_frame)]} == {1000.}
        report["clips"][name] = dict(duration_s=seconds,decoded_frames=int(counts[-1]),
                                            decoding="passed",gif=info,
                                            inspected_frame_times_s=times[name])
    for name,record in manifest["files"].items():
        assert sha(a.media/name)==record["sha256"], name
    report["all_manifest_media_hashes_verified"] = True
    (qa/"media-check.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
