#!/usr/bin/env python3
import re
import sys
import zipfile

GPL_MARKERS = {
    b"the GNU General Public License, version 2 or later": "a GPL-2+ VLC module",
    b"H.264/MPEG-4 AVC codec - Copy": "x264 (GPL)",
    b"pp_postprocess": "libpostproc (GPL)",
    b"dvdnav_open": "libdvdnav (GPL)",
    b"DVDOpen": "libdvdread (GPL)",
    b"Real RTSP": "VLC's Real RTSP access (GPL)",
    b"vbi_decode_teletext_8301_cni": "zvbi teletext (GPL-2 only)",
    b"LIVE555 Streaming Media": "live555 (LGPL-3)",
    b"Lua interpreter": "VLC's Lua module (GPL)",
    b"'--enable-live555'": "libVLC configured with live555",
    b"'--enable-dvdread'": "libVLC configured with dvdread",
}

FFMPEG_FORBIDDEN_FLAGS = ("--enable-gpl", "--enable-version3", "--enable-nonfree")
FFMPEG_CUT_DECODERS = {
    b"Two slices reporting being the first in the same frame.": "HEVC (hevcdec.c)",
    b"Filters may change only once per access unit.": "TrueHD/MLP (mlpdec.c)",
    b"SBR was found before the first channel element.": "AAC (aacdec)",
}


def ffmpeg_configurations(data):
    lines = [m.group(0).decode(errors="replace") for m in re.finditer(rb"--prefix=[^\x00]{0,8000}", data)]
    return [line for line in lines if "--disable-doc" in line.split() or "--disable-everything" in line.split()]


def check(path):
    problems = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if re.search(r"(^|/)assets/lua/|\.luac?$", name):
                problems.append(f"{name}: Lua script (GPL-2+)")
                continue
            if not name.endswith(".so"):
                continue
            data = archive.read(name)
            for marker, what in GPL_MARKERS.items():
                if marker in data:
                    problems.append(f"{name}: {what}")
            for marker, decoder in FFMPEG_CUT_DECODERS.items():
                if marker in data:
                    problems.append(f"{name}: FFmpeg decoder {decoder} built in")
            for config in ffmpeg_configurations(data):
                for flag in FFMPEG_FORBIDDEN_FLAGS:
                    if flag in config.split():
                        problems.append(f"{name}: FFmpeg configured {flag}")
    return problems


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    failed = False
    for path in sys.argv[1:]:
        problems = check(path)
        for problem in problems:
            print(f"{path}: {problem}")
        failed = failed or bool(problems)
        if not problems:
            print(f"{path}: no GPL parts, no cut decoders")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
