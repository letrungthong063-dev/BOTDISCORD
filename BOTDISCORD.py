import sys
sys.modules['audioop'] = None
import discord
from discord.ext import commands
from PIL import Image
import aiohttp
import os
import io
import shutil
import zipfile
import time
from io import BytesIO
from colorama import Fore, Style, init
init(autoreset=True)

# ================== TOKEN BOT ==================
TOKEN = os.getenv("TOKEN")
# ================================================================

start_time = time.time()
BASE_DIR = "data"
START_TIME = time.time()

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================== HÀM XỬ LÝ ẢNH (TỪ botlogo1.py) ==================
async def add_border_with_template(input_bytes, output_path, template_path="frame.png"):
    with Image.open(template_path).convert("RGBA") as frame:
        with Image.open(input_bytes).convert("RGBA") as img:
            img = img.resize(frame.size)
            new_img = Image.new("RGBA", frame.size)
            new_img.paste(img, (0, 0))
            new_img.paste(frame, (0, 0), frame)
            new_img.save(output_path, "PNG")

# ================== HÀM PHỤ TRỢ (TỪ botzip1.py) ==================
def get_folder_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total

def format_uptime(seconds: float):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d > 0:
        parts.append(f"{d}d")
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

# ================== SỰ KIỆN on_ready ==================
@bot.event
async def on_ready():
    uptime_seconds = int(time.time() - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    print(Fore.GREEN + "✅ BOT ĐÃ SẴN SÀNG")
    print(Fore.CYAN + "======================================")
    print(Fore.YELLOW + f"🤖 Tên bot     : {bot.user.name}")
    print(Fore.YELLOW + f"🆔 ID bot      : {bot.user.id}")
    print(Fore.MAGENTA + f"🌐 Số server   : {len(bot.guilds)}")
    total_users = sum(g.member_count for g in bot.guilds)
    print(Fore.BLUE + f"👥 Tổng user   : {total_users}")
    print(Fore.CYAN + f"📺 Tổng kênh   : {sum(len(g.channels) for g in bot.guilds)}")
    print(Fore.GREEN + f"⏱️ Uptime      : {hours}h {minutes}m {seconds}s")
    print(Fore.CYAN + "======================================")

# ================== SỰ KIỆN VÀ LỆNH CỦA BOTLOGO1.PY ==================
# ================== XÓA NỀN ẢNH (MULTI API KEY) ==================

REMOVE_BG_KEYS = [
    "83rp9ZcT42TUqQoSoZ2h8jCE",
    "pmK76vPnr1TJqTcwKgPBwYf5",
    "dv6b3gRzsNz3A5DgcamN5S1z",
    "J4KU6AYopjzrAKKNMKGJcsWL",
    "XoCsyCWs357PP7NdGNWJM8CJ",
    "XCgP2QXMbtqskm99fEwaS1rL",
    "kKUZRHZhaEp1CLUgPoYza7da",
    "C1GqJwPLwCNNx3Md6Tb7dmjW",
    "aZFLhcwM1XRnXVUZhywZj9UW",
    "C2uNsBuQ4bBMaxATX1QTTPuT",
    "oGTC8Jx2jR8XhuxRWCTdxfpr",
]

async def remove_bg(img_bytes: bytes) -> bytes:
    """Gửi ảnh lên remove.bg API, thử nhiều API key nếu bị lỗi."""
    url = "https://api.remove.bg/v1.0/removebg"
    last_error = None

    for api_key in REMOVE_BG_KEYS:
        data = aiohttp.FormData()
        data.add_field("image_file", img_bytes, filename="image.png", content_type="image/png")
        data.add_field("size", "auto")
        headers = {"X-Api-Key": api_key}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as r:
                if r.status == 200:
                    print(f"[REMOVE.BG] ✅ Thành công với API: {api_key}")
                    return await r.read()
                else:
                    text = await r.text()
                    last_error = f"API {api_key} lỗi {r.status}: {text}"
                    print(f"[REMOVE.BG] ⚠️ {last_error}")

    # Nếu tất cả API đều fail
    raise RuntimeError(f"❌ Tất cả API key đều lỗi. Lỗi cuối cùng: {last_error}")


@bot.command()
async def rmbg(ctx):
    """Xóa nền ảnh (reply vào tin nhắn có ảnh hoặc gửi kèm ảnh)."""
    attachments = []

    # Nếu người dùng reply vào một tin nhắn có ảnh
    if ctx.message.reference and ctx.message.reference.resolved:
        ref_msg = ctx.message.reference.resolved
        attachments.extend(ref_msg.attachments)

    # Nếu người dùng gửi ảnh kèm theo lệnh
    attachments.extend(ctx.message.attachments)

    if not attachments:
        await ctx.reply("❌ Vui lòng reply vào ảnh hoặc đính kèm ảnh.")
        return

    processing_message = await ctx.reply("⏳ Đang xử lý ảnh...")
    files = []

    for i, a in enumerate(attachments, start=1):
        try:
            img_bytes = await a.read()
            out_bytes = await remove_bg(img_bytes)
            files.append(discord.File(io.BytesIO(out_bytes), filename=f"no_bg_{i}.png"))
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi xử lý {a.filename}: {e}")

    if files:
        await processing_message.edit(content="✅ Đã xoá nền xong!")
        await ctx.send(files=files)
    else:
        await processing_message.edit(content="❌ Không xử lý được ảnh nào.")

import json

async def get_api_quota(api_key: str) -> dict:
    """Lấy thông tin quota còn lại từ remove.bg cho 1 API key"""
    url = "https://api.remove.bg/v1.0/account"
    headers = {"X-Api-Key": api_key}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                return await r.json()
            else:
                text = await r.text()
                raise RuntimeError(f"Lỗi {r.status}: {text}")


@bot.command()
async def listrmbg(ctx):
    """Xem số lượt remove.bg còn lại cho tất cả API key và tổng cộng"""
    results = []
    total_all = 0

    for i, api_key in enumerate(REMOVE_BG_KEYS, start=1):
        try:
            data = await get_api_quota(api_key)
            api_info = data["data"]["attributes"]["api"]

            free_calls = api_info.get("free_calls", 0)
            payg_credits = api_info.get("payg_credits", 0)
            sub_credits = api_info.get("subscription", {}).get("credits", 0)

            total = free_calls + payg_credits + sub_credits
            total_all += total

            results.append(f"🔑 API {i}: **{total} lượt** còn lại")
        except Exception as e:
            results.append(f"🔑 API {i}: ❌ Lỗi khi kiểm tra ({e})")

    msg = "📊 **Trạng thái API remove.bg**\n\n" + "\n".join(results)
    msg += f"\n\n📌 **TỔNG CỘNG: {total_all} lượt còn lại**"
    await ctx.reply(msg)

@bot.command()
async def border(ctx, *, arg: str = None):
    if not arg or "id:" not in arg:
        await ctx.reply("❌ Sai cú pháp! Dùng: `!border id:<tên_file>` (VD: !border id:1)")
        return

    frame_id = arg.split("id:")[1].strip()
    template_path = f"{frame_id}.png"

    if not os.path.exists(template_path):
        await ctx.reply(f"⚠️ Không tìm thấy file khung **{template_path}**!")
        return

    if not ctx.message.reference:
        await ctx.reply("⚠️ Bạn phải reply vào một tin nhắn có ảnh!")
        return

    replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    if not replied_message.attachments:
        await ctx.reply("⚠️ Tin nhắn bạn reply không có ảnh!")
        return

    processing_message = await ctx.reply("🔄 Đang xử lý...")

    output_files = []
    try:
        async with aiohttp.ClientSession() as session:
            for i, attachment in enumerate(replied_message.attachments, start=1):
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.read()

                output_path = f"output_{i}.png"
                await add_border_with_template(BytesIO(data), output_path, template_path)
                output_files.append(discord.File(output_path))

        if output_files:
            await processing_message.edit(content=f"✨ Đã thêm khung từ **{template_path}**!")
            await ctx.send(files=output_files)
            for f in output_files:
                try:
                    os.remove(f.fp.name)
                except:
                    pass
        else:
            await processing_message.edit(content="❌ Không xử lý được ảnh nào!")
    except Exception as e:
        print("❌ Error:", e)
        await processing_message.edit(content="❌ Có lỗi xảy ra khi xử lý ảnh!")


from PIL import ImageDraw

# ====== HÀM CẮT ẢNH THÀNH HÌNH TRÒN ======
async def make_circle_image(input_bytes, output_path):
    with Image.open(input_bytes).convert("RGBA") as img:
        size = min(img.size)  # lấy cạnh nhỏ nhất để đảm bảo hình vuông
        img = img.resize((size, size))

        # Tạo mask hình tròn
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)

        # Áp mask vào ảnh
        circular_img = Image.new("RGBA", (size, size))
        circular_img.paste(img, (0, 0), mask=mask)

        circular_img.save(output_path, "PNG")


# ====== LỆNH !circle ======
@bot.command()
async def circle(ctx):
    if not ctx.message.reference:
        await ctx.reply("⚠️ Bạn phải reply vào một tin nhắn có ảnh!")
        return

    replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    if not replied_message.attachments:
        await ctx.reply("⚠️ Tin nhắn bạn reply không có ảnh!")
        return

    processing_message = await ctx.reply("🔄 Đang xử lý...")

    output_files = []
    try:
        async with aiohttp.ClientSession() as session:
            for i, attachment in enumerate(replied_message.attachments, start=1):
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.read()

                output_path = f"circle_{i}.png"
                await make_circle_image(BytesIO(data), output_path)
                output_files.append(discord.File(output_path))

        if output_files:
            await processing_message.edit(content="✨ Ảnh đã được cắt thành hình tròn!")
            await ctx.send(files=output_files)
            for f in output_files:
                try:
                    os.remove(f.fp.name)
                except:
                    pass
        else:
            await processing_message.edit(content="❌ Không xử lý được ảnh nào!")

    except Exception as e:
        print("❌ Error:", e)
        await processing_message.edit(content="❌ Có lỗi xảy ra khi xử lý ảnh!")

# ================== CÁC LỆNH TỪ BOTZIP1.PY ==================
@bot.command()
async def create(ctx, folder: str):
    path = os.path.join(BASE_DIR, folder)
    if os.path.exists(path):
        await ctx.send("❌ Thư mục đã tồn tại!")
        return
    os.makedirs(path)
    await ctx.reply(f"📂 Đã tạo thư mục **{folder}**")

@bot.command()
async def add(ctx, *, arg: str):
    if not ctx.message.reference:
        await ctx.reply("❌ Hãy reply vào tin nhắn chứa ảnh để thêm.")
        return
    try:
        folder, names = arg.split(":")
        folder = folder.strip()
        names = [n.strip() for n in names.split(",")]
    except:
        await ctx.reply("❌ Sai cú pháp! Dùng: `!add <thư_mục>: tên1,tên2,...`")
        return
    ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    attachments = ref_msg.attachments
    if len(attachments) != len(names):
        await ctx.reply("❌ Số lượng ảnh và số lượng tên không khớp!")
        return
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        await ctx.reply("❌ Thư mục không tồn tại!")
        return
    status_msg = await ctx.reply("🔄 Đang xử lý...")
    for i, attachment in enumerate(attachments):
        filename = f"{names[i]}.png"
        filepath = os.path.join(folder_path, filename)
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                    img = Image.open(io.BytesIO(img_bytes))
                    img = img.convert("RGBA")
                    img.save(filepath, format="PNG")
    await status_msg.edit(content=f"✅ Đã thêm {len(names)} ảnh vào thư mục **{folder}**")

@bot.command()
async def zip(ctx, folder: str):
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        await ctx.reply("❌ Thư mục không tồn tại!")
        return
    status_msg = await ctx.reply("🔄 Đang xử lý...")
    zip_path = os.path.join(BASE_DIR, f"{folder}.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    size = os.path.getsize(zip_path)
    if size <= 25 * 1024 * 1024:
        await status_msg.edit(content=f"✅ Nén thư mục **{folder}** thành công!")
        await ctx.send(file=discord.File(zip_path))
    else:
        await status_msg.edit(content=f"⚠️ File zip quá nặng ({size/1024/1024:.2f} MB), không thể gửi qua Discord.")
    os.remove(zip_path)

@bot.command()
async def delete(ctx, folder: str):
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        await ctx.reply("❌ Thư mục không tồn tại!")
        return
    msg = await ctx.reply(f"⚠️ Bạn có chắc muốn xoá thư mục **{folder}** không?\nNhấn ✅ để xác nhận hoặc ❌ để huỷ.")
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    def check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == msg.id
        )
    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        if str(reaction.emoji) == "✅":
            shutil.rmtree(folder_path)
            await ctx.reply(f"🗑️ Đã xoá thư mục **{folder}**")
        else:
            await ctx.reply("❌ Đã huỷ lệnh xoá.")
    except:
        await ctx.reply("⌛ Hết thời gian xác nhận, lệnh xoá đã bị huỷ.")

@bot.command()
async def list(ctx):
    folders = os.listdir(BASE_DIR)
    if not folders:
        await ctx.reply("📂 Không có thư mục nào.")
        return
    msg = "📂 Danh sách thư mục:\n\n"
    for folder in folders:
        folder_path = os.path.join(BASE_DIR, folder)
        if os.path.isdir(folder_path):
            count = len(os.listdir(folder_path))
            size = get_folder_size(folder_path) / 1024
            msg += f"📂 {folder} | 📸 {count} ảnh | 📦 {size:.2f} KB\n"
    await ctx.reply(msg)

@bot.command()
async def helpme(ctx):
    help_text = """
📖 **Hướng dẫn sử dụng Bot**

━━━━━━━━━━━━━━━━━━━━━━
🗂️ **QUẢN LÝ THƯ MỤC**
`!create <tên_thư_mục>` → Tạo thư mục chứa ảnh  
`!list` → Liệt kê thư mục hiện có  
`!delete <thư_mục>` → Xoá thư mục (có xác nhận)  
`!deleteimg <tên_thư_mục>: <tên_ảnh>`→Xoá ảnh trong thư mục.
`!zip <thư_mục>` → Nén thư mục thành file .zip  

━━━━━━━━━━━━━━━━━━━━━━
🖼️ **QUẢN LÝ ẢNH**
`!add <thư_mục>: tên1,tên2,...` (reply tin nhắn có ảnh) → Thêm ảnh PNG  
`!show <thư_mục>` → Hiển thị ảnh trong thư mục  
`!rename <thư_mục>: <tên_cũ>=<tên_mới>` → Đổi tên ảnh  

━━━━━━━━━━━━━━━━━━━━━━
🎨 **KHUNG ẢNH**
`!border id:<tên_file>` (reply ảnh) → Thêm khung cho ảnh  
`!listframe` → Xem danh sách các file khung có sẵn .
`!circle`→Cắt ảnh thành hình tròn
━━━━━━━━━━━━━━━━━━━━━━
⚙️ **HỆ THỐNG**
`!helpme` → Xem hướng dẫn này  
`!status` → Xem trạng thái bot  

━━━━━━━━━━━━━━━━━━━━━━
👑 **Admin**: trungthong0714
"""
    await ctx.reply(help_text)

@bot.command()
async def status(ctx):
    uptime = format_uptime(time.time() - START_TIME)
    latency = round(bot.latency * 1000, 2)
    server_count = len(bot.guilds)
    embed = discord.Embed(title="📊 Trạng thái Bot", color=0x00ff99)
    embed.add_field(name="👑 Admin", value="trungthong0714", inline=False)
    embed.add_field(name="🌐 Số server", value=str(server_count), inline=True)
    embed.add_field(name="⏱️ Uptime", value=uptime, inline=True)
    embed.add_field(name="💡 Tình trạng", value="Online ✅", inline=True)
    embed.add_field(name="⚡ Tốc độ", value=f"{latency} ms", inline=True)
    await ctx.reply(embed=embed)

@bot.command()
async def rename(ctx, *, arg: str):
    try:
        folder, names = arg.split(":")
        folder = folder.strip()
        old_name, new_name = names.strip().split("=", 1)
        old_name = old_name.strip()
        new_name = new_name.strip()
    except:
        await ctx.reply("❌ Sai cú pháp! Dùng: `!rename <thư_mục>: <tên_cũ>=<tên_mới>`")
        return
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        await ctx.reply("❌ Thư mục không tồn tại!")
        return
    old_file = None
    for f in os.listdir(folder_path):
        name, ext = os.path.splitext(f)
        if name == old_name:
            old_file = os.path.join(folder_path, f)
            new_file = os.path.join(folder_path, f"{new_name}{ext}")
            break
    if not old_file:
        await ctx.reply(f"❌ Ảnh **{old_name}** không tồn tại trong thư mục **{folder}**")
        return
    if os.path.exists(new_file):
        await ctx.reply(f"⚠️ Ảnh **{new_name}{ext}** đã tồn tại trong thư mục **{folder}**")
        return
    os.rename(old_file, new_file)
    await ctx.reply(f"✅ Đã đổi tên ảnh **{os.path.basename(old_file)}** thành **{os.path.basename(new_file)}** trong thư mục **{folder}**")

@bot.command()
async def show(ctx, folder: str):
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        await ctx.reply("❌ Thư mục không tồn tại!")
        return
    files = [f for f in os.listdir(folder_path) if f.endswith(".png")]
    if not files:
        await ctx.reply("📂 Thư mục này chưa có ảnh nào.")
        return
    chunk_size = 10
    for i in range(0, len(files), chunk_size):
        batch = files[i:i+chunk_size]
        file_paths = [os.path.join(folder_path, f) for f in batch]
        discord_files = [discord.File(fp, filename=os.path.basename(fp)) for fp in file_paths]
        caption = "📸 Danh sách ảnh:\n" + "\n".join([f"• {f}" for f in batch])
        await ctx.reply(content=caption, files=discord_files)


@bot.command()
async def listframe(ctx):
    # Lấy tất cả file PNG trong thư mục
    frames = [f for f in os.listdir() if f.lower().endswith(".png")]

    if not frames:
        await ctx.reply("❌ Không tìm thấy khung nào trong thư mục bot.")
        return

    # Giới hạn số lượng file gửi trong 1 lần (tránh vượt giới hạn Discord)
    max_files_per_msg = 10
    for i in range(0, len(frames), max_files_per_msg):
        batch = frames[i:i + max_files_per_msg]
        files_to_send = [discord.File(f, filename=f) for f in batch]
        caption = "📂 **Danh sách khung khả dụng:**\n" + "\n".join([f"• {f}" for f in batch])
        await ctx.reply(content=caption, files=files_to_send)

@bot.listen("on_command")
async def log_command(ctx):
    user = f"{ctx.author} (ID: {ctx.author.id})"
    guild = ctx.guild.name if ctx.guild else "DM"
    channel = ctx.channel.name if ctx.guild else "DM"

    print(
        Fore.CYAN + "📢 [INFO] " +
        Fore.YELLOW + f"{user} " +
        Fore.GREEN + f"Use !{ctx.command} " +
        Fore.MAGENTA + f"at {guild}#{channel} " +
        Fore.WHITE + f"| Content: {ctx.message.content}"
    )


@bot.command()
async def deleteimg(ctx, *, arg: str):
    try:
        folder, img_name = arg.split(":")
        folder = folder.strip()
        img_name = img_name.strip()
    except:
        await ctx.reply("❌ Sai cú pháp! Dùng: `!deleteimg <thư_mục>: <tên_ảnh>`")
        return

    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.exists(folder_path):
        await ctx.reply("❌ Thư mục không tồn tại!")
        return

    # Tìm file ảnh trong thư mục
    target_file = None
    for f in os.listdir(folder_path):
        name, ext = os.path.splitext(f)
        if name == img_name:
            target_file = os.path.join(folder_path, f)
            break

    if not target_file:
        await ctx.reply(f"❌ Ảnh **{img_name}** không tồn tại trong thư mục **{folder}**")
        return

    # Xác nhận trước khi xoá
    msg = await ctx.reply(f"⚠️ Bạn có chắc muốn xoá ảnh **{img_name}** trong thư mục **{folder}** không?\nNhấn ✅ để xác nhận hoặc ❌ để huỷ.")
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == msg.id
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        if str(reaction.emoji) == "✅":
            os.remove(target_file)
            await ctx.reply(f"🗑️ Đã xoá ảnh **{img_name}** trong thư mục **{folder}**")
        else:
            await ctx.reply("❌ Đã huỷ lệnh xoá.")
    except:
        await ctx.reply("⌛ Hết thời gian xác nhận, lệnh xoá đã bị huỷ.")


@bot.event
async def on_command_error(ctx, error):
    # Nếu lệnh không tồn tại
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply(f"❌ Lệnh bạn nhập không tồn tại. Gõ `!helpme` để xem danh sách lệnh.")
    else:
        # In lỗi ra terminal để debug
        print(f"[ERROR] {error}")

@bot.command()
async def botinfo(ctx):
    """Hiển thị thông tin cơ bản của bot"""
    embed = discord.Embed(title="🤖 Thông tin Bot", color=0x3498db)
    embed.add_field(name="Tên Bot", value=bot.user.name, inline=True)
    embed.add_field(name="ID Bot", value=bot.user.id, inline=True)
    embed.add_field(name="Số server", value=len(bot.guilds), inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency*1000, 2)} ms", inline=True)
    embed.add_field(name="Uptime", value=format_uptime(time.time()-START_TIME), inline=False)
    embed.set_footer(text=f"Yêu cầu bởi {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.reply(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """Hiển thị thông tin server"""
    if ctx.guild is None:
        await ctx.reply("❌ Lệnh này chỉ dùng trong server!")
        return
    guild = ctx.guild
    embed = discord.Embed(title=f"🌐 Thông tin Server: {guild.name}", color=0x2ecc71)
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Số thành viên", value=guild.member_count, inline=True)
    embed.add_field(name="Số kênh", value=len(guild.channels), inline=True)
    embed.add_field(name="Chủ sở hữu", value=guild.owner, inline=False)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await ctx.reply(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    """Hiển thị thông tin về một user"""
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 Thông tin người dùng: {member}", color=0xe67e22)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Tên", value=member.display_name, inline=True)
    embed.add_field(name="Tham gia server", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    embed.add_field(name="Tạo tài khoản", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    await ctx.reply(embed=embed)

@bot.command()
async def guildinfo(ctx):
    """Hiển thị danh sách các server mà bot đang tham gia"""
    guilds = bot.guilds
    if not guilds:
        await ctx.reply("❌ Bot chưa tham gia server nào.")
        return

    description = ""
    for g in guilds:
        description += f"• **{g.name}** (ID: {g.id}) | 👥 {g.member_count} thành viên\n"

    embed = discord.Embed(title="🌐 Danh sách Server", description=description, color=0x1abc9c)
    embed.set_footer(text=f"Tổng cộng: {len(guilds)} server")
    await ctx.reply(embed=embed)


# ================== CHẠY BOT ==================
bot.run(TOKEN)

