"""Bot Telegram da Antenna Hair com agendamento no Google Calendar."""
from __future__ import annotations

import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from google_calendar import CalendarError, create_booking_event
from salon_logic import SalonBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logic = SalonBot()
gemini = None


def maybe_load_gemini():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("Gemini desativado: GEMINI_API_KEY não foi encontrada neste terminal.")
        return None
    try:
        from gemini_client import GeminiClient
        client = GeminiClient()
        logger.info("Gemini ativado com sucesso (chave encontrada; valor oculto).")
        return client
    except Exception as exc:
        logger.warning("Gemini não foi ativado. Motivo: %s", exc)
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user and update.message:
        await update.message.reply_text(logic.reset(update.effective_user.id), parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user and update.message:
        await update.message.reply_text(logic.reset(update.effective_user.id), parse_mode="Markdown")


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    text = update.message.text
    response = logic.respond(user_id, text)

    if response.startswith("Não identifiquei") and gemini is not None:
        response = await asyncio.to_thread(gemini.answer, text)
        await update.message.reply_text(response, parse_mode="Markdown")
        return

    if response.startswith("Vou verificar a disponibilidade"):
        booking = logic.take_confirmed_booking(user_id)
        if not booking:
            await update.message.reply_text("Não consegui recuperar seu pedido. Envie o serviço desejado para começar novamente.")
            return
        booking["user_id"] = user_id
        try:
            event = await asyncio.to_thread(create_booking_event, booking)
            await update.message.reply_text(
                "Agendamento confirmado! ✅\n\n"
                f"• Serviço: *{booking['service'].name}*\n"
                f"• Cliente: *{booking['customer_name']}*\n"
                f"• Data e horário: *{booking['appointment_date']} às {booking['appointment_time']}*\n"
                f"• Valor: *R$ {booking['service'].price},00*\n\n"
                "O evento foi criado na agenda do Antenna Hair.",
                parse_mode="Markdown",
            )
            logger.info("Evento criado no Google Calendar: %s", event.get("id"))
        except CalendarError as exc:
            await update.message.reply_text(
                f"Não consegui confirmar esse horário: {exc}\n\nQual horário você prefere?",
                parse_mode="Markdown",
            )
        except Exception:
            logger.exception("Falha inesperada ao criar evento no Google Calendar")
            await update.message.reply_text(
                "Não consegui acessar a agenda agora. Tente novamente em instantes.",
                parse_mode="Markdown",
            )
        return

    await update.message.reply_text(response, parse_mode="Markdown")


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Erro: defina TELEGRAM_BOT_TOKEN antes de executar.")
    global gemini
    gemini = maybe_load_gemini()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancelar", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    logger.info("Bot Antenna Hair iniciado com integração Google Calendar.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
