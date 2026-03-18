import pygame
import pygame.scrap
import sys
import re
import random

# ── Grid constants (fixed logical size) ───────────────────────────────────────
COLS, ROWS  = 16, 10
GROUND_ROW  = ROWS - 2
PANEL_MIN_W = 280
PANEL_MAX_W = 420
MIN_WIN_W   = 700
MIN_WIN_H   = 480
FPS         = 60
STEP_MS     = 220

# ── Colors ────────────────────────────────────────────────────────────────────
BG           = (8,  12,  26)
GRID_LINE    = (40, 70, 160, 40)
PLAT_TOP     = (42, 74, 170)
PLAT_SIDE    = (26, 46, 110)
PLAT_SHINE   = (100, 160, 255, 30)
PANEL_BG     = (12, 16, 32)
PANEL_BORDER = (40, 60, 130)
TEXT_DIM     = (80, 110, 160)
TEXT_MAIN    = (180, 210, 255)
TEXT_ERR     = (255, 100, 100)
TEXT_OK      = (80, 200, 140)
CURSOR_COL   = (74, 170, 255)
SEL_COL      = (74, 170, 255, 60)
STAR_COL     = (180, 210, 255)
BOT_BODY     = (192, 216, 255)
BOT_SUIT     = (26,  42,  94)
BOT_VISOR    = (68, 170, 255)
BOT_TRIM     = (138, 180, 255)

random.seed(42)
STAR_DATA = [(random.random(), random.random(), random.uniform(0.4, 1.8)) for _ in range(70)]


# ── Parser ─────────────────────────────────────────────────────────────────────
def parse(source: str):
    lines = source.split('\n')
    cmds, i = [], 0
    while i < len(lines):
        raw      = lines[i]
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        m = re.fullmatch(r'repeat\s+(\d+)', stripped)
        if m:
            n, body = int(m.group(1)), []
            i += 1
            while i < len(lines):
                inner = lines[i]
                if inner and inner[0] in (' ', '\t'):
                    body.append(inner.strip())
                    i += 1
                else:
                    break
            if not body:
                raise ValueError(f"'repeat {n}' has no indented body")
            for _ in range(n):
                cmds.extend(body)
        else:
            cmds.append(stripped)
            i += 1
    return cmds


# ── Interpreter ────────────────────────────────────────────────────────────────
VALID = {'move right', 'move left', 'jump', 'dash', 'crouch', 'wait', 'flip'}

def execute(cmds):
    x, y, d = 1, GROUND_ROW - 1, 1
    frames = [(x, y, d)]
    for cmd in cmds:
        if cmd not in VALID:
            raise ValueError(f"Unknown command: '{cmd}'")
        if   cmd == 'move right': x = min(x + 1, COLS - 1)
        elif cmd == 'move left':  x = max(x - 1, 0)
        elif cmd == 'jump':
            frames.append((x, max(y - 1, 0), d))
            x = min(max(x + d, 0), COLS - 1)
            y = min(y, GROUND_ROW - 1)
        elif cmd == 'dash':   x = min(max(x + d * 2, 0), COLS - 1)
        elif cmd == 'crouch': y = min(y + 1, GROUND_ROW - 1)
        elif cmd == 'wait':   pass
        elif cmd == 'flip':   d = -d
        frames.append((x, y, d))
    return frames


# ── Drawing helpers ────────────────────────────────────────────────────────────
def draw_bg(surf, gw, gh):
    surf.fill(BG)
    for rx, ry, rr in STAR_DATA:
        pygame.draw.circle(surf, (*STAR_COL, 180), (int(rx * gw), int(ry * gh)), max(1, int(rr)))

def draw_grid(surf, gw, gh, cell):
    s = pygame.Surface((gw, gh), pygame.SRCALPHA)
    for c in range(COLS + 1):
        pygame.draw.line(s, GRID_LINE, (c * cell, 0), (c * cell, gh))
    for r in range(ROWS + 1):
        pygame.draw.line(s, GRID_LINE, (0, r * cell), (gw, r * cell))
    surf.blit(s, (0, 0))

def draw_ground(surf, cell):
    for col in range(COLS):
        px, py = col * cell, GROUND_ROW * cell
        pygame.draw.rect(surf, PLAT_TOP,  (px+1, py+1,   cell-2, 8))
        pygame.draw.rect(surf, PLAT_SIDE, (px+1, py+9,   cell-2, cell-10))
        sh = pygame.Surface((cell-2, 3), pygame.SRCALPHA)
        sh.fill(PLAT_SHINE)
        surf.blit(sh, (px+1, py+1))

def draw_bot(surf, gx, gy, d, cell):
    cx = gx * cell + cell // 2
    cy = gy * cell + cell // 2
    sc = cell / 48
    tmp = pygame.Surface((cell, cell), pygame.SRCALPHA)
    hx, hy = cell // 2, cell // 2
    def s(v): return max(1, int(v * sc))
    pygame.draw.circle(tmp, BOT_BODY,  (hx,       hy - s(10)), s(10))
    pygame.draw.circle(tmp, BOT_SUIT,  (hx,       hy - s(10)), s(8))
    pygame.draw.ellipse(tmp, BOT_VISOR,(hx-s(2),  hy-s(16),   s(6),  s(5)))
    pygame.draw.rect(tmp, BOT_BODY,    (hx+s(2),  hy-s(20),   s(3),  s(5)))
    pygame.draw.rect(tmp, BOT_BODY,    (hx-s(7),  hy-s(1),    s(14), s(12)))
    pygame.draw.rect(tmp, BOT_SUIT,    (hx-s(5),  hy,         s(10), s(10)))
    pygame.draw.rect(tmp, BOT_TRIM,    (hx-s(3),  hy+s(1),    s(6),  s(5)))
    pygame.draw.rect(tmp, BOT_BODY,    (hx-s(11), hy,         s(5),  s(9)))
    pygame.draw.rect(tmp, BOT_BODY,    (hx+s(6),  hy,         s(5),  s(9)))
    pygame.draw.rect(tmp, BOT_BODY,    (hx-s(6),  hy+s(11),   s(5),  s(7)))
    pygame.draw.rect(tmp, BOT_BODY,    (hx+s(1),  hy+s(11),   s(5),  s(7)))
    if d < 0:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (cx - cell // 2, cy - cell // 2))


# ── Editor ─────────────────────────────────────────────────────────────────────
class Editor:
    def __init__(self, font):
        self.font   = font
        self.lines  = ['move right', 'move right', 'jump', 'move right', 'move right', '']
        self.cur_l  = len(self.lines) - 1
        self.cur_c  = 0
        self.sel_l  = None
        self.sel_c  = None
        self.scroll = 0

    def _clamp_col(self, l, c):
        return max(0, min(c, len(self.lines[l])))

    def _set_cursor(self, l, c, extend_sel=False):
        if extend_sel:
            if self.sel_l is None:
                self.sel_l, self.sel_c = self.cur_l, self.cur_c
        else:
            self.sel_l = self.sel_c = None
        self.cur_l = max(0, min(l, len(self.lines) - 1))
        self.cur_c = self._clamp_col(self.cur_l, c)

    def _sel_range(self):
        if self.sel_l is None:
            return None
        a = (self.sel_l, self.sel_c)
        b = (self.cur_l, self.cur_c)
        if (a[0], a[1]) > (b[0], b[1]):
            a, b = b, a
        return a[0], a[1], b[0], b[1]

    def _selected_text(self):
        r = self._sel_range()
        if r is None:
            return ''
        sl, sc, el, ec = r
        if sl == el:
            return self.lines[sl][sc:ec]
        parts = [self.lines[sl][sc:]]
        for i in range(sl + 1, el):
            parts.append(self.lines[i])
        parts.append(self.lines[el][:ec])
        return '\n'.join(parts)

    def _delete_selection(self):
        r = self._sel_range()
        if r is None:
            return
        sl, sc, el, ec = r
        self.lines[sl:el+1] = [self.lines[sl][:sc] + self.lines[el][ec:]]
        self._set_cursor(sl, sc)

    def handle_key(self, event):
        ctrl  = event.mod & pygame.KMOD_CTRL
        shift = event.mod & pygame.KMOD_SHIFT
        k = event.key

        # select-all
        if ctrl and k == pygame.K_a:
            self.sel_l, self.sel_c = 0, 0
            self.cur_l = len(self.lines) - 1
            self.cur_c = len(self.lines[self.cur_l])
            return
        # copy
        if ctrl and k == pygame.K_c:
            txt = self._selected_text()
            if txt:
                pygame.scrap.put(pygame.SCRAP_TEXT, txt.encode())
            return
        # cut
        if ctrl and k == pygame.K_x:
            txt = self._selected_text()
            if txt:
                pygame.scrap.put(pygame.SCRAP_TEXT, txt.encode())
                self._delete_selection()
            return
        # paste
        if ctrl and k == pygame.K_v:
            raw = pygame.scrap.get(pygame.SCRAP_TEXT)
            if raw:
                try:
                    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n').rstrip('\x00')
                except Exception:
                    return
                if self.sel_l is not None:
                    self._delete_selection()
                parts  = text.split('\n')
                before = self.lines[self.cur_l][:self.cur_c]
                after  = self.lines[self.cur_l][self.cur_c:]
                if len(parts) == 1:
                    self.lines[self.cur_l] = before + parts[0] + after
                    self.cur_c = len(before) + len(parts[0])
                else:
                    new = [before + parts[0]] + parts[1:-1] + [parts[-1] + after]
                    self.lines[self.cur_l:self.cur_l+1] = new
                    self.cur_l += len(parts) - 1
                    self.cur_c  = len(parts[-1])
                self.sel_l = self.sel_c = None
            return

        # navigation
        if k == pygame.K_UP:
            self._set_cursor(self.cur_l - 1, self.cur_c, shift); return
        if k == pygame.K_DOWN:
            self._set_cursor(self.cur_l + 1, self.cur_c, shift); return
        if k == pygame.K_LEFT:
            if shift or self.sel_l is None:
                nc, nl = self.cur_c - 1, self.cur_l
                if nc < 0 and nl > 0:
                    nl -= 1; nc = len(self.lines[nl])
                self._set_cursor(nl, max(0, nc), shift)
            else:
                r = self._sel_range()
                if r: self._set_cursor(r[0], r[1])
            return
        if k == pygame.K_RIGHT:
            if shift or self.sel_l is None:
                nc, nl = self.cur_c + 1, self.cur_l
                if nc > len(self.lines[nl]) and nl < len(self.lines) - 1:
                    nl += 1; nc = 0
                self._set_cursor(nl, nc, shift)
            else:
                r = self._sel_range()
                if r: self._set_cursor(r[2], r[3])
            return
        if k == pygame.K_HOME:
            self._set_cursor(self.cur_l, 0, shift); return
        if k == pygame.K_END:
            self._set_cursor(self.cur_l, len(self.lines[self.cur_l]), shift); return

        # editing
        if k == pygame.K_RETURN:
            if self.sel_l is not None: self._delete_selection()
            rest = self.lines[self.cur_l][self.cur_c:]
            self.lines[self.cur_l] = self.lines[self.cur_l][:self.cur_c]
            self.cur_l += 1
            self.lines.insert(self.cur_l, rest)
            self.cur_c = 0
            return
        if k == pygame.K_BACKSPACE:
            if self.sel_l is not None:
                self._delete_selection(); return
            if self.cur_c > 0:
                l = self.lines[self.cur_l]
                self.lines[self.cur_l] = l[:self.cur_c-1] + l[self.cur_c:]
                self.cur_c -= 1
            elif self.cur_l > 0:
                prev_len = len(self.lines[self.cur_l - 1])
                self.lines[self.cur_l-1] += self.lines.pop(self.cur_l)
                self.cur_l -= 1
                self.cur_c  = prev_len
            return
        if k == pygame.K_DELETE:
            if self.sel_l is not None:
                self._delete_selection(); return
            l = self.lines[self.cur_l]
            if self.cur_c < len(l):
                self.lines[self.cur_l] = l[:self.cur_c] + l[self.cur_c+1:]
            elif self.cur_l < len(self.lines) - 1:
                self.lines[self.cur_l] += self.lines.pop(self.cur_l + 1)
            return
        if k == pygame.K_TAB:
            if self.sel_l is not None: self._delete_selection()
            l = self.lines[self.cur_l]
            self.lines[self.cur_l] = l[:self.cur_c] + '    ' + l[self.cur_c:]
            self.cur_c += 4
            return

        if event.unicode and event.unicode.isprintable() and not ctrl:
            if self.sel_l is not None: self._delete_selection()
            l = self.lines[self.cur_l]
            self.lines[self.cur_l] = l[:self.cur_c] + event.unicode + l[self.cur_c:]
            self.cur_c += 1

    def get_source(self):
        return '\n'.join(self.lines)

    def draw(self, surf, rect, focused, tick):
        lh  = self.font.get_linesize()
        pad = 8
        visible = max(1, (rect.h - pad * 2) // lh)

        if self.cur_l < self.scroll:
            self.scroll = self.cur_l
        if self.cur_l >= self.scroll + visible:
            self.scroll = self.cur_l - visible + 1

        pygame.draw.rect(surf, (14, 20, 45), rect, border_radius=6)
        border_col = CURSOR_COL if focused else PANEL_BORDER
        pygame.draw.rect(surf, border_col, rect, 1, border_radius=6)

        old_clip = surf.get_clip()
        surf.set_clip(rect.inflate(-2, -2))

        sel_range = self._sel_range()

        for i in range(visible):
            li = i + self.scroll
            if li >= len(self.lines):
                break
            text = self.lines[li]
            ty   = rect.y + pad + i * lh

            if sel_range:
                sl, sc, el, ec = sel_range
                if sl <= li <= el:
                    hsc = sc if li == sl else 0
                    hec = ec if li == el else len(text)
                    x1  = rect.x + pad + self.font.size(text[:hsc])[0]
                    x2  = rect.x + pad + self.font.size(text[:hec])[0]
                    if x2 <= x1: x2 = x1 + self.font.size(' ')[0]
                    sel_surf = pygame.Surface((x2 - x1, lh), pygame.SRCALPHA)
                    sel_surf.fill(SEL_COL)
                    surf.blit(sel_surf, (x1, ty))

            color = TEXT_MAIN if li == self.cur_l else TEXT_DIM
            surf.blit(self.font.render(text, True, color), (rect.x + pad, ty))

            if focused and li == self.cur_l and (tick // 30) % 2 == 0:
                cx = rect.x + pad + self.font.size(text[:self.cur_c])[0]
                pygame.draw.line(surf, CURSOR_COL, (cx, ty), (cx, ty + lh - 2), 2)

        surf.set_clip(old_clip)


# ── Button ─────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, label, font, bg, hover):
        self.label = label
        self.font  = font
        self.bg    = bg
        self.hover = hover
        self.rect  = pygame.Rect(0, 0, 10, 10)

    def draw(self, surf):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf, self.hover if hovered else self.bg, self.rect, border_radius=6)
        pygame.draw.rect(surf, PANEL_BORDER, self.rect, 1, border_radius=6)
        ts = self.font.render(self.label, True, TEXT_MAIN)
        surf.blit(ts, ts.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


# ── CMD reference ──────────────────────────────────────────────────────────────
CMD_REF = [
    ('move right', 'step right'),
    ('move left',  'step left'),
    ('jump',       'arc up + forward'),
    ('dash',       'leap 2 forward'),
    ('crouch',     'duck down'),
    ('wait',       'skip a step'),
    ('flip',       'reverse direction'),
    ('repeat N',   'loop N times'),
]


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.scrap.init()
    pygame.key.set_repeat(400, 40)

    screen = pygame.display.set_mode((1080, 560), pygame.RESIZABLE)
    pygame.display.set_caption("Code-O-Naut")
    clock  = pygame.time.Clock()

    try:
        mono  = pygame.font.SysFont('Courier New', 15)
        small = pygame.font.SysFont('Courier New', 13)
    except Exception:
        mono  = pygame.font.SysFont(None, 16)
        small = pygame.font.SysFont(None, 14)

    editor    = Editor(mono)
    run_btn   = Button('▶  run',   mono,  (22, 40, 100), (34, 58, 140))
    reset_btn = Button('↺  reset', small, (16, 24,  60), (24, 36,  90))

    frames       = [(1, GROUND_ROW - 1, 1)]
    anim_idx     = 0
    anim_accum   = 0
    running_anim = False
    status_msg   = ''
    status_col   = TEXT_DIM
    tick         = 0
    editor_focused = True
    editor_rect    = pygame.Rect(0, 0, 0, 0)  # updated each frame

    def do_run():
        nonlocal frames, anim_idx, anim_accum, running_anim, status_msg, status_col
        try:
            cmds   = parse(editor.get_source())
            frames = execute(cmds)
            anim_idx = anim_accum = 0
            running_anim = True
            n = len(cmds)
            status_msg = f'{n} command{"s" if n != 1 else ""} — running...'
            status_col = TEXT_DIM
        except ValueError as e:
            status_msg = str(e)
            status_col = TEXT_ERR
            running_anim = False

    def do_reset():
        nonlocal frames, anim_idx, running_anim, status_msg, status_col
        frames = [(1, GROUND_ROW - 1, 1)]
        anim_idx = 0
        running_anim = False
        status_msg = 'reset'
        status_col = TEXT_DIM
        editor.lines = ['']
        editor.cur_l = editor.cur_c = 0
        editor.sel_l = editor.sel_c = None

    while True:
        dt   = clock.tick(FPS)
        tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                editor_focused = editor_rect.collidepoint(event.pos)

            if editor_focused and event.type == pygame.KEYDOWN:
                if (event.mod & pygame.KMOD_CTRL) and event.key == pygame.K_r:
                    do_run()
                else:
                    editor.handle_key(event)

            if run_btn.clicked(event):   do_run()
            if reset_btn.clicked(event): do_reset()

        # advance animation
        if running_anim:
            anim_accum += dt
            while anim_accum >= STEP_MS:
                anim_accum -= STEP_MS
                anim_idx   += 1
                if anim_idx >= len(frames):
                    anim_idx     = len(frames) - 1
                    running_anim = False
                    status_msg   = f'done ({len(frames)-1} steps)'
                    status_col   = TEXT_OK
                    break

        # ── layout ────────────────────────────────────────────────────────────
        ww, wh  = screen.get_size()
        ww      = max(ww, MIN_WIN_W)
        wh      = max(wh, MIN_WIN_H)

        panel_w = max(PANEL_MIN_W, min(PANEL_MAX_W, int(ww * 0.28)))
        grid_w  = ww - panel_w
        grid_h  = wh
        cell    = min(grid_w // COLS, grid_h // ROWS)
        draw_gw = COLS * cell
        draw_gh = ROWS * cell
        grid_ox = (grid_w - draw_gw) // 2
        grid_oy = (grid_h - draw_gh) // 2

        PAD      = 12
        px       = grid_w + PAD
        pw       = panel_w - PAD * 2
        lh_m     = mono.get_linesize()
        lh_s     = small.get_linesize()

        # Fixed-height panel items (from bottom up)
        HINT_H   = lh_s + PAD
        # Command ref: header + rows
        ref_rows = len(CMD_REF)
        REF_H    = lh_s + 4 + ref_rows * (lh_s + 2)
        # Status
        STATUS_H = lh_s + 6
        # Buttons
        BTN_H    = 32
        SBTN_H   = 26
        LABEL_H  = lh_m + 4

        # editor stretches to fill remaining vertical space
        fixed_below_editor = BTN_H + 6 + SBTN_H + 8 + STATUS_H + 10 + REF_H + HINT_H
        editor_h = max(60, wh - PAD - LABEL_H - 6 - fixed_below_editor - PAD)

        # compute y positions top-down
        y = PAD
        label_y    = y;                         y += LABEL_H + 4
        editor_rect = pygame.Rect(px, y, pw, editor_h); y += editor_h + 6
        run_btn.rect   = pygame.Rect(px, y, pw, BTN_H);  y += BTN_H + 6
        reset_btn.rect = pygame.Rect(px, y, pw, SBTN_H); y += SBTN_H + 8
        status_y   = y;                         y += STATUS_H + 10
        ref_start  = y

        # ── draw grid ─────────────────────────────────────────────────────────
        grid_surf = pygame.Surface((grid_w, grid_h))
        draw_bg(grid_surf, grid_w, grid_h)
        sub = pygame.Surface((draw_gw, draw_gh))
        sub.fill(BG)
        draw_grid(sub, draw_gw, draw_gh, cell)
        draw_ground(sub, cell)
        fx, fy, fd = frames[anim_idx]
        draw_bot(sub, fx, fy, fd, cell)
        grid_surf.blit(sub, (grid_ox, grid_oy))
        screen.blit(grid_surf, (0, 0))

        # ── draw panel ─────────────────────────────────────────────────────────
        pygame.draw.rect(screen, PANEL_BG, (grid_w, 0, panel_w, wh))
        pygame.draw.line(screen, PANEL_BORDER, (grid_w, 0), (grid_w, wh))

        # label
        screen.blit(mono.render('your program', True, TEXT_DIM), (px, label_y))

        # editor
        editor.draw(screen, editor_rect, editor_focused, tick)

        # buttons
        run_btn.draw(screen)
        reset_btn.draw(screen)

        # status (one line, never overflows)
        if status_msg:
            msg = status_msg
            while msg and small.size(msg)[0] > pw:
                msg = msg[:-1]
            screen.blit(small.render(msg, True, status_col), (px, status_y))

        # command reference (stop drawing rows that would overlap hint)
        ry       = ref_start
        hint_top = wh - HINT_H
        screen.blit(small.render('commands', True, TEXT_DIM), (px, ry))
        ry += lh_s + 4
        for cmd, desc in CMD_REF:
            if ry + lh_s > hint_top:
                break
            cs = small.render(cmd, True, CURSOR_COL)
            screen.blit(cs, (px, ry))
            # description: truncate to remaining width
            avail = pw - cs.get_width() - 6
            d_txt = '  ' + desc
            while d_txt and small.size(d_txt)[0] > avail:
                d_txt = d_txt[:-1]
            screen.blit(small.render(d_txt, True, TEXT_DIM), (px + cs.get_width(), ry))
            ry += lh_s + 2

        # hint pinned to bottom
        screen.blit(small.render('ctrl+R = run', True, (40, 60, 100)), (px, wh - HINT_H))

        pygame.display.flip()


if __name__ == '__main__':
    main()