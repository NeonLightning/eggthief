import random, sys, ctypes, random, os, json, array, math
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame

pygame.init()
pygame.mouse.set_visible(False)
LOGICAL_WIDTH, LOGICAL_HEIGHT = 640, 480
game_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
WIN = pygame.display.set_mode((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Jewel Thief")
if sys.platform == "win32":
    hwnd = pygame.display.get_wm_info()['window']
    ctypes.windll.user32.ShowWindow(hwnd, 3) 
# Colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE = (0, 100, 255)
GOLD = (255, 215, 0)
BLACK = (0, 0, 0)
FPS = 60
clock = pygame.time.Clock()
PLAYER_SIZE = 32
GUARD_SIZE = 32
JEWEL_SIZE = 16
enemy_sprites_all = []
enemy_sprites_pool = []
HIGHSCORE_FILE = "highscores.json"
MAX_HIGHSCORES = 10

def create_ding(frequency=1880, duration_ms=150, volume=0.2, sample_rate=44100):
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array("h")
    for i in range(n_samples):
        t = i / sample_rate
        sample = volume * math.sin(2 * math.pi * frequency * t)
        sample *= math.exp(-5 * t)
        buf.append(int(sample * 32767))
    stereo = array.array("h")
    for s in buf:
        stereo.append(s)
        stereo.append(s)
    return pygame.mixer.Sound(buffer=stereo.tobytes())

def create_dong(frequency=380, duration_ms=150, volume=0.2, sample_rate=44100):
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array("h")
    for i in range(n_samples):
        t = i / sample_rate
        sample = volume * math.sin(2 * math.pi * frequency * t)
        sample *= math.exp(-5 * t)
        buf.append(int(sample * 32767))
    stereo = array.array("h")
    for s in buf:
        stereo.append(s)
        stereo.append(s)
    return pygame.mixer.Sound(buffer=stereo.tobytes())

def load_all_enemy_sprites(folder="sprites/enemies"):
    valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not os.path.isdir(folder):
        return []
    images = []
    for fname in os.listdir(folder):
        if fname.lower().endswith(valid_exts):
            path = os.path.join(folder, fname)
            try:
                img = pygame.image.load(path).convert_alpha()
                images.append(img)
            except Exception as e:
                print(f"Could not load enemy sprite {path}: {e}")
    return images

def load_random_background(folder="backgrounds"):
    valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
    if not files:
        return None
    chosen_file = random.choice(files)
    path = os.path.join(folder, chosen_file)
    try:
        img = pygame.image.load(path).convert()
        img = pygame.transform.scale(img, (LOGICAL_WIDTH, LOGICAL_HEIGHT))
        return img
    except Exception as e:
        print(f"Failed to load background image {path}: {e}")
        return None

def load_random_enemy_sprite(folder="sprites/enemies", size=(GUARD_SIZE, GUARD_SIZE)):
    valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
    if not files:
        return None
    chosen_file = random.choice(files)
    path = os.path.join(folder, chosen_file)
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except Exception as e:
        print(f"Failed to load enemy sprite {path}: {e}")
        return None

def random_color():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            image_path = os.path.join("sprites", "thief.png")
            full_image = pygame.image.load(image_path).convert_alpha()
            full_image = pygame.transform.scale(full_image, (PLAYER_SIZE, PLAYER_SIZE))
            self.image = full_image
            mask = pygame.mask.from_surface(full_image)
            tight_rect = mask.get_bounding_rects()[0]
            self.rect = tight_rect.copy()
            self.rect.center = (LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40)
            self.image = full_image.subsurface(tight_rect).copy()
        except Exception as e:
            print(f"Failed to load player sprite: {e}")
            self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
            self.image.fill(BLUE)
            self.rect = self.image.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT - 40))
        self.speed = 4

class Guard(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed, sprite=None):
        super().__init__()
        if sprite:
            self.image = sprite.copy()
        else:
            self.image = pygame.Surface((GUARD_SIZE, GUARD_SIZE), pygame.SRCALPHA)
            self.image.fill(RED)
        mask = pygame.mask.from_surface(self.image)
        rects = mask.get_bounding_rects()
        if rects:
            tight_rect = rects[0]
            self.image = self.image.subsurface(tight_rect).copy()
            self.rect = self.image.get_rect(topleft=(x + tight_rect.x, y + tight_rect.y))
        else:
            self.rect = self.image.get_rect(topleft=(x, y))
        self.dir_x, self.dir_y = direction
        self.speed = speed

    def update(self):
        self.rect.x += self.dir_x * self.speed
        self.rect.y += self.dir_y * self.speed
        if self.rect.left < 0 or self.rect.right > LOGICAL_WIDTH:
            self.dir_x *= -1
        if self.rect.top < 0 or self.rect.bottom > LOGICAL_HEIGHT:
            self.dir_y *= -1

class Jewel(pygame.sprite.Sprite):
    def __init__(self, x, y, level):
        super().__init__()
        try:
            base_img = pygame.image.load("sprites/gem.png").convert_alpha()
            base_img = pygame.transform.scale(base_img, (JEWEL_SIZE * 2, JEWEL_SIZE * 2))  # Scale if needed
            tint_color = [0, 0, 0]
            tint_color[level % 3] = 255
            tint_surface = pygame.Surface(base_img.get_size(), pygame.SRCALPHA)
            tint_surface.fill((*tint_color, 0))  # Alpha 0 keeps transparency
            tinted_img = base_img.copy()
            tinted_img.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            mask = pygame.mask.from_surface(tinted_img)
            rects = mask.get_bounding_rects()
            if rects:
                tight_rect = rects[0]
                self.image = tinted_img.subsurface(tight_rect).copy()
                self.rect = self.image.get_rect(center=(x, y))
            else:
                self.image = tinted_img
                self.rect = self.image.get_rect(center=(x, y))
        except Exception as e:
            print(f"Failed to load or tint gem: {e}")
            self.image = pygame.Surface((JEWEL_SIZE, JEWEL_SIZE))
            self.image.fill(GOLD)
            self.rect = self.image.get_rect(center=(x, y))

def random_guard_direction():
    choices = [
        (1, 0), (-1, 0),
        (0, 1), (0, -1),
        (1, 1), (-1, 1), (1, -1), (-1, -1)
    ]
    return random.choice(choices)

def spawn_level(level, all_sprites, guards, jewels, player):
    global enemy_sprites_pool
    if enemy_sprites_all:
        last_sprite = enemy_sprites_pool[-1] if enemy_sprites_pool else None
        candidates = [s for s in enemy_sprites_all if s != last_sprite]
        if candidates:
            new_sprite = random.choice(candidates)
        else:
            new_sprite = random.choice(enemy_sprites_all)
        enemy_sprites_pool.append(new_sprite)

    guards.empty()
    jewels.empty()
    all_sprites.empty()
    all_sprites.add(player)

    # Spawn jewels
    for _ in range(10):
        x = random.randint(40, LOGICAL_WIDTH - 40)
        y = random.randint(40, LOGICAL_HEIGHT - 80)
        jewel = Jewel(x, y, level)
        all_sprites.add(jewel)
        jewels.add(jewel)

    # Spawn guards away from player
    num_guards = min(level, len(enemy_sprites_pool))
    sprites_for_guards = random.sample(enemy_sprites_pool, k=num_guards)
    min_distance = 100  # Minimum distance from player in pixels

    for sprite in sprites_for_guards:
        for _ in range(100):  # Try up to 100 times to find a valid spawn point
            x = random.randint(0, LOGICAL_WIDTH - GUARD_SIZE)
            y = random.randint(0, LOGICAL_HEIGHT - GUARD_SIZE)
            dist_x = abs(x + GUARD_SIZE // 2 - player.rect.centerx)
            dist_y = abs(y + GUARD_SIZE // 2 - player.rect.centery)
            if (dist_x ** 2 + dist_y ** 2) ** 0.5 >= min_distance:
                direction = random_guard_direction()
                speed = round(random.uniform(1.5, 3.5), 1)
                guard = Guard(x, y, direction, speed, sprite)
                guards.add(guard)
                all_sprites.add(guard)
                break

def draw_text(surface, text, size, color, x, y):
    font = pygame.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, rect)

def load_highscores():
    if not os.path.isfile(HIGHSCORE_FILE):
        return []
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_highscores(scores):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(scores, f)

def add_highscore(name, score, level):
    scores = load_highscores()
    scores.append({"name": name, "score": score, "level": level})
    scores.sort(key=lambda s: s["score"], reverse=True)
    scores = scores[:MAX_HIGHSCORES]
    save_highscores(scores)
    return scores

def is_highscore(score):
    scores = load_highscores()
    return len(scores) < MAX_HIGHSCORES or score > min(s["score"] for s in scores)

def show_game_over(score, level):
    WIN.fill(BLACK)
    draw_text(WIN, "GAME OVER", 48, RED, WIN.get_width() // 2, WIN.get_height() // 2 - 100)
    draw_text(WIN, f"Score: {score}", 32, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 - 60)
    draw_text(WIN, f"Level Reached: {level}", 32, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 - 30)
    if is_highscore(score):
        draw_text(WIN, "New High Score! Enter your name:", 24, GOLD, WIN.get_width() // 2, WIN.get_height() // 2 + 10)
        pygame.display.flip()
        name = ""
        default_name = "Player"
        typed = False
        active = True
        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not typed:
                            name = default_name
                        active = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        if len(name) < 10 and event.unicode.isprintable():
                            name += event.unicode
                            typed = True
            temp_name = name if name or typed else default_name
            WIN.fill(BLACK)
            draw_text(WIN, "GAME OVER", 48, RED, WIN.get_width() // 2, WIN.get_height() // 2 - 100)
            draw_text(WIN, f"Score: {score}", 32, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 - 60)
            draw_text(WIN, f"Level Reached: {level}", 32, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 - 30)
            draw_text(WIN, "New High Score!", 36, GOLD, WIN.get_width() // 2, 100)
            draw_text(WIN, "Enter Your Name:", 28, WHITE, WIN.get_width() // 2, 180)
            draw_text(WIN, temp_name, 36, WHITE, WIN.get_width() // 2, 240)
            pygame.display.flip()
        add_highscore(name, score, level)
    scores = load_highscores()
    WIN.fill(BLACK)
    draw_text(WIN, "GAME OVER", 48, RED, WIN.get_width() // 2, WIN.get_height() // 2 - 100)
    draw_text(WIN, f"Score: {score}", 32, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 - 60)
    draw_text(WIN, f"Level Reached: {level}", 32, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 - 30)
    draw_text(WIN, "High Scores:", 32, GOLD, WIN.get_width() // 2, WIN.get_height() // 2 + 100)
    for i, entry in enumerate(scores):
        text = f"{i+1}. {entry['name']} - {entry['score']} (Lv {entry['level']})"
        draw_text(WIN, text, 24, WHITE, WIN.get_width() // 2, WIN.get_height() // 2 + 130 + i * 30)
    draw_text(WIN, "Press Enter to play again.", 24, WHITE, WIN.get_width() // 2, WIN.get_height() - 40)
    draw_text(WIN, "Press any other key to exit...", 24, WHITE, WIN.get_width() // 2, WIN.get_height() - 20)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Quit game
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                else:
                    return False

def main():
    global WIN
    enemy_sprites_all[:] = load_all_enemy_sprites()
    level = 1
    score = 0
    running = True
    player = Player()
    all_sprites = pygame.sprite.Group()
    jewels = pygame.sprite.Group()
    guards = pygame.sprite.Group()

    def load_new_background():
        nonlocal bg_image, bg_color
        bg_image = load_random_background("backgrounds")
        if bg_image is None:
            bg_color = random_color()
        else:
            bg_color = None
            
    spawn_level(level, all_sprites, guards, jewels, player)
    bg_image = None
    bg_color = None
    load_new_background()
    ding = create_ding()
    dong = create_dong()
    while running:
        clock.tick(FPS)
        if bg_image:
            game_surface.blit(bg_image, (0,0))
        else:
            game_surface.fill(bg_color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                WIN = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        mouse_x, mouse_y = pygame.mouse.get_pos()
        scale_x = LOGICAL_WIDTH / WIN.get_width()
        scale_y = LOGICAL_HEIGHT / WIN.get_height()
        logical_mouse_pos = (mouse_x * scale_x, mouse_y * scale_y)
        player.rect.center = (int(logical_mouse_pos[0]), int(logical_mouse_pos[1]))
        guards.update()
        collected = pygame.sprite.spritecollide(player, jewels, True)
        if collected:
            ding.play()
            score += len(collected)
        if pygame.sprite.spritecollideany(player, guards):
            dong.play()
            if show_game_over(score, level):
                level = 1
                score = 0
                spawn_level(level, all_sprites, guards, jewels, player)
                load_new_background()
            else:
                break
        all_sprites.draw(game_surface)
        draw_text(game_surface, f"Level: {level}", 24, WHITE, 60, 20)
        draw_text(game_surface, f"Score: {score}", 24, WHITE, LOGICAL_WIDTH - 80, 20)
        scaled_surface = pygame.transform.smoothscale(game_surface, WIN.get_size())
        WIN.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        if not jewels:
            draw_text(game_surface, "LEVEL COMPLETE!", 36, GOLD, LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2)
            scaled_surface = pygame.transform.smoothscale(game_surface, WIN.get_size())
            WIN.blit(scaled_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(1500)
            level += 1
            spawn_level(level, all_sprites, guards, jewels, player)
            load_new_background()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()