import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Bot sozlamalari (O'zingizning TOKEN va Admin ID raqamingizni yozing)
BOT_TOKEN = "8925391424:AAEbz7-sTH5g5zYOmJTFMTp3babkuikiZF4"
ADMIN_ID = 8353037526  # Sizning Telegram ID'ingiz

logging.basicConfig(level=logging.INFO)
router = Router()

# Holatlar (FSM)
class PaymentState(StatesGroup):
    waiting_for_receipt = State()

# /start buyrug'i
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(PaymentState.waiting_for_receipt)
    await message.answer(
        "👋 Assalomu alaykum! <b>LadyWear</b> do'konimizga xush kelibsiz.\n\n"
        "💳 Iltimos, xarid uchun amalga oshirgan <b>to'lov chekingizni (rasm ko'rinishida)</b> ushbu botga yuboring:",
        parse_mode="HTML"
    )

# Mijoz rasm yuborganda
@router.message(PaymentState.waiting_for_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    user = message.from_user
    
    user_info = (
        f"📩 <b>YANGI TO'LOV CHEKI KELDI!</b>\n\n"
        f"👤 <b>Mijoz:</b> {user.full_name} (@{user.username, 'Nomaʼlum'})"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
        f"Holat: Admin tasdiqi kutilmoqda..."
    )

    # Admin uchun tasdiqlash tugmalari
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"reject_{user.id}")
        ]
    ])

    # Rasmni adminga yuborish
    await message.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=user_info,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await message.answer("✅ Chekingiz qabul qilindi! Admin tekshirib chiqqach, tez orada sizga xabar beramiz.")
    await state.clear()

# Rasm bo'lmagan narsa yuborilganda
@router.message(PaymentState.waiting_for_receipt)
async def not_photo(message: Message):
    await message.answer("⚠️ Iltimos, matn emas, <b>to'lov chekining rasmini</b> yuboring!", parse_mode="HTML")

# Admin tugmani bosganda (Tasdiqlash yoki Rad etish)
@router.callback_query(F.data.startswith(("approve_", "reject_")))
async def admin_callback(callback: CallbackQuery):
    action, user_id = callback.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        # Mijozga xabar berish
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text="🎉 <b>Tabriklaymiz!</b> To'lovingiz muvaffaqiyatli tasdiqlandi va buyurtmangiz faol holatga o'tdi ✅ Tez orada yetkazib beramiz!",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Mijozga xabar yuborib bo'lmadi: {e}")

        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n<b>STATUS: ✅ TASDIQLANGAN</b>",
            parse_mode="HTML",
            reply_markup=None
        )
        await callback.answer("Buyurtma tasdiqlandi!")

    elif action == "reject":
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text="❌ Afsuski, to'lov chekingiz tasdiqlanmadi yoki mablag' tushmadi. Iltimos, qaytadan tekshirib urinib ko'ring.",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Mijozga xabar yuborib bo'lmadi: {e}")

        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n<b>STATUS: ❌ RAD ETILGAN</b>",
            parse_mode="HTML",
            reply_markup=None
        )
        await callback.answer("Buyurtma rad etildi!")

# Botni ishga tushirish
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())