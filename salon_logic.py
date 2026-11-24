"""Lógica do chatbot Antenna Hair com fluxo de agendamento."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional


@dataclass(frozen=True)
class Service:
    name: str
    price: int
    duration_minutes: int
    aliases: tuple[str, ...]


SERVICES: tuple[Service, ...] = (
    Service("Alongamento", 100, 120, ("alongamento", "alongameto", "alongamento de unha", "extensao")),
    Service("Manutenção", 90, 120, ("manutencao", "manutencao alongamento", "manutencao de unha", "manutençao")),
    Service("Esmaltação em gel", 70, 120, ("esmaltacao em gel", "esmaltacao gel", "esmaltas em gel", "esmalte em gel")),
    Service("Blindagem", 70, 120, ("blindagem", "blindajem", "blindagem de unha")),
    Service("Banho de gel", 70, 120, ("banho de gel", "banho gel", "banh de gel")),
    Service("Remoção", 50, 120, ("remocao", "remoçao", "remover alongamento", "tirar alongamento")),
    Service("Unhas tradicionais", 30, 120, ("unhas tradicionais", "unha tradicional", "manicure tradicional")),
    Service("Cutilagem", 20, 120, ("cutilagem", "cuticula", "cutilagem", "cutilajen")),
)

WEEKDAYS = {
    "segunda": 0, "terca": 1, "quarta": 2, "quinta": 3,
    "sexta": 4, "sabado": 5, "domingo": 6,
}

NUMBER_WORDS = {
    "um": 1, "dois": 2, "tres": 3, "quatro": 4, "cinco": 5,
    "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
    "onze": 11, "doze": 12, "treze": 13, "quatorze": 14,
    "quinze": 15, "dezesseis": 16, "dezessete": 17, "dezoito": 18,
    "dezenove": 19, "vinte": 20, "vinte e um": 21, "vinte e dois": 22,
    "vinte e tres": 23, "vinte e quatro": 24, "vinte e cinco": 25,
    "vinte e seis": 26, "vinte e sete": 27, "vinte e oito": 28,
    "vinte e nove": 29, "trinta": 30, "trinta e um": 31,
}

MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().strip())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9\s/:\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def menu_text() -> str:
    lines = ["💅 *Tabela de serviços – Antenna Hair*"]
    for service in SERVICES:
        lines.append(f"• {service.name}: *R$ {service.price},00*")
    return "\n".join(lines)


def is_information_question(text: str) -> bool:
    value = normalize(text)
    markers = (
        "quais servicos", "que servicos", "servicos voces", "servicos tem",
        "voces fazem unhas", "atendimento de unhas", "tabela de servicos",
        "precos", "preco", "quanto custa", "valor da", "valor do",
    )
    return any(marker in value for marker in markers)


def is_service_selection(text: str) -> bool:
    value = normalize(text)
    if is_information_question(text):
        return False
    starters = (
        "quero ", "gostaria de ", "quero fazer ", "vou fazer ",
        "agendar ", "marcar ", "escolho ", "fazer ", "servico ",
    )
    return value.startswith(starters) or find_service(text) is not None


def service_price_answer(text: str) -> Optional[str]:
    service = find_service(text)
    if not service or not is_information_question(text):
        return None
    return f"{service.name} custa *R$ {service.price},00*."


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def find_service(text: str) -> Optional[Service]:
    value = normalize(text)
    if not value:
        return None
    for service in SERVICES:
        for alias in service.aliases:
            if normalize(alias) in value:
                return service
    best: tuple[float, Optional[Service]] = (0.0, None)
    words = value.split()
    for service in SERVICES:
        for alias in service.aliases:
            alias_words = normalize(alias).split()
            scores = [max((_similarity(word, alias_word) for word in words), default=0) for alias_word in alias_words]
            score = sum(scores) / len(scores)
            if score > best[0]:
                best = score, service
    return best[1] if best[0] >= 0.76 else None


def parse_date(text: str, today: Optional[date] = None) -> Optional[date]:
    today = today or date.today()
    value = normalize(text)
    if re.search(r"\bhoje\b", value):
        return today
    if re.search(r"\bamanha\b", value):
        return today + timedelta(days=1)
    match = re.search(r"\b(\d{1,2})\s+(?:do|de)\s+(\d{1,2})(?:\s+(?:de|do)\s+)?(\d{2,4})?\b", value)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            return None
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", value)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            result = date(year, month, day)
            return result
        except ValueError:
            return None
    for month_name, month_number in MONTHS.items():
        if month_name in value:
            day_match = re.search(r"\b(?:dia\s+)?(\d{1,2})\b", value)
            if not day_match:
                return None
            try:
                return date(today.year, month_number, int(day_match.group(1)))
            except ValueError:
                return None
    for word, number in NUMBER_WORDS.items():
        if re.search(rf"\bdia\s+{re.escape(word)}\b", value):
            month = today.month
            try:
                result = date(today.year, month, number)
            except ValueError:
                return None
            if result < today:
                next_month = 1 if month == 12 else month + 1
                year = today.year + 1 if month == 12 else today.year
                try:
                    result = date(year, next_month, number)
                except ValueError:
                    return None
            return result
    day_only = re.search(r"\bdia\s+(\d{1,2})\b", value)
    if day_only:
        number = int(day_only.group(1))
        month = today.month
        try:
            result = date(today.year, month, number)
        except ValueError:
            return None
        if result < today:
            next_month = 1 if month == 12 else month + 1
            year = today.year + 1 if month == 12 else today.year
            return date(year, next_month, number)
        return result
    for name, weekday in WEEKDAYS.items():
        if name in value:
            delta = (weekday - today.weekday()) % 7
            return today + timedelta(days=delta or 7)
    return None


def parse_time(text: str) -> Optional[tuple[int, int]]:
    value = normalize(text)
    # Aceita frases como “prefiro às 16h”, “às 9 horas”, “17h” e “14:30”.
    match = re.search(
        r"(?<!\d)(\d{1,2})(?:\s*(?:h|horas?)\s*(\d{2})?|\s*:\s*(\d{2}))?(?!\d)",
        value,
    )
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or match.group(3) or 0)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return hour, minute


def is_date_text(text: str) -> bool:
    value = normalize(text)
    return bool(
        re.search(r"\d{1,2}[/-]\d{1,2}", value)
        or re.search(r"\d{1,2}\s+(?:do|de)\s+\d{1,2}", value)
        or "dia " in value
        or any(month in value for month in MONTHS)
    )


def is_unavailable_date(chosen_date: date) -> bool:
    return chosen_date.weekday() in {0, 6}


def next_available_dates(start: date, count: int = 3) -> str:
    dates: list[str] = []
    candidate = start
    while len(dates) < count:
        if not is_unavailable_date(candidate):
            dates.append(candidate.strftime("%d/%m/%Y"))
        candidate += timedelta(days=1)
    return ", ".join(dates)


class SalonBot:
    """Fluxo: serviço → nome → data → horário → confirmação."""

    def __init__(self) -> None:
        self.sessions: dict[int, dict[str, object]] = {}
        self.confirmed_bookings: dict[int, dict[str, object]] = {}

    def reset(self, user_id: int) -> str:
        self.sessions[user_id] = {"step": "service"}
        self.confirmed_bookings.pop(user_id, None)
        return (
            "Olá! Eu sou a assistente virtual da *Antenna Hair*.\n\n"
            + menu_text()
        )

    def respond(self, user_id: int, text: str) -> str:
        text = text.strip()
        normalized = normalize(text)
        session = self.sessions.setdefault(user_id, {"step": "service"})

        if normalized in {"/start", "oi", "ola", "menu", "precos", "preco"}:
            return self.reset(user_id)
        if normalized in {"/cancelar", "cancelar", "reiniciar", "comecar de novo", "voltar"}:
            return self.reset(user_id)

        step = session.get("step")

        # Uma nova cliente pode iniciar outro atendimento enviando o serviço,
        # sem precisar enviar /start novamente.
        if step != "service" and is_service_selection(text):
            self.reset(user_id)
            session = self.sessions[user_id]
            step = "service"

        if step == "service":
            if normalized in {"oi", "ola", "bom dia", "boa tarde", "boa noite"}:
                return "Olá! Qual serviço você deseja?"
            if is_information_question(text):
                price_answer = service_price_answer(text)
                if price_answer:
                    return price_answer
                return menu_text()
            service = find_service(text)
            if not service or not is_service_selection(text):
                return "Não consegui identificar o serviço."
            session.update({"step": "name", "service": service, "service_name": service.name, "price": service.price})
            return "Qual é o seu nome?"

        if step == "name":
            detected_service = find_service(text)
            if detected_service and len(normalized.split()) <= 4:
                session.update({"service": detected_service, "service_name": detected_service.name, "price": detected_service.price})
                return "Qual é o seu nome?"
            if len(text) < 2:
                return "Qual é o seu nome?"
            session.update({"step": "date", "customer_name": text})
            return "Qual dia você deseja?"

        if step == "date":
            chosen_date = parse_date(text)
            if not chosen_date:
                return "Qual dia você deseja?"
            if chosen_date < date.today():
                return "Essa data já passou. Informe uma data futura."
            if is_unavailable_date(chosen_date):
                return (
                    f"Não trabalho aos domingos nem às segundas-feiras. "
                    f"Os próximos dias disponíveis são: *{next_available_dates(chosen_date + timedelta(days=1))}*. "
                    "Qual dia você deseja?"
                )
            session.update({"step": "time", "appointment_date": chosen_date.isoformat()})
            return "Qual horário você prefere?"

        if step == "time":
            if is_date_text(text):
                corrected_date = parse_date(text)
                if corrected_date and not is_unavailable_date(corrected_date) and corrected_date >= date.today():
                    session["appointment_date"] = corrected_date.isoformat()
                    return "Data corrigida. Qual horário você prefere?"
                if corrected_date and is_unavailable_date(corrected_date):
                    return f"Não trabalho aos domingos nem às segundas-feiras. Próximos dias disponíveis: *{next_available_dates(corrected_date + timedelta(days=1))}*. Qual dia você deseja?"
            parsed_time = parse_time(text)
            if not parsed_time:
                return "Qual horário você prefere?"
            hour, minute = parsed_time
            if hour < 9 or hour > 16 or (hour == 16 and minute > 0):
                return "Esse horário não está disponível. Qual horário você prefere?"
            session.update({"step": "confirmation", "appointment_time": f"{hour:02d}:{minute:02d}"})
            service = session["service"]
            return (
                "Confira seu pedido:\n\n"
                f"• Serviço: *{service.name}*\n"
                f"• Valor: *R$ {service.price},00*\n"
                f"• Nome: *{session['customer_name']}*\n"
                f"• Data: *{datetime.fromisoformat(session['appointment_date']).strftime('%d/%m/%Y')}*\n"
                f"• Horário: *{hour:02d}:{minute:02d}*\n\n"
                "Responda *sim* para verificar a disponibilidade e criar o agendamento, ou *não* para cancelar."
            )

        if step == "confirmation":
            if normalized in {"sim", "s", "confirmo", "confirmar", "yes"}:
                session["step"] = "pending_calendar"
                self.confirmed_bookings[user_id] = dict(session)
                return "Vou verificar a disponibilidade na agenda. Aguarde um instante..."
            if normalized in {"nao", "n", "não", "cancelar"}:
                return self.reset(user_id)
            return "Responda *sim* para confirmar ou *não* para cancelar."

        if step == "pending_calendar":
            return "Seu pedido está sendo processado. Se precisar recomeçar, digite /cancelar."
        return self.reset(user_id)

    def take_confirmed_booking(self, user_id: int) -> Optional[dict[str, object]]:
        return self.confirmed_bookings.pop(user_id, None)


if __name__ == "__main__":
    bot = SalonBot()
    print(bot.reset(1))
    for message in ("quero um alongameto", "Valentina", "amanhã", "14h", "sim"):
        print("\n---\n", bot.respond(1, message))
