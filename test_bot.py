from salon_logic import SalonBot, find_service, parse_date, parse_time


def test_typo_is_understood():
    assert find_service("quero um alongameto").name == "Alongamento"
    assert find_service("blindajem").name == "Blindagem"
    assert find_service("banh de gel").name == "Banho de gel"
    assert find_service("esmaltacao em gel").name == "Esmaltação em gel"


def test_information_questions_do_not_start_booking():
    bot = SalonBot()
    menu = bot.respond(20, "quais serviços vocês oferecem?")
    assert "Tabela de serviços" in menu
    assert "Qual é o seu nome?" not in menu
    price = bot.respond(20, "quanto custa a blindagem?")
    assert "Blindagem" in price
    assert "R$ 70,00" in price
    assert "Qual é o seu nome?" not in price


def test_parsers():
    assert parse_date("01/12/2026").isoformat() == "2026-12-01"
    assert parse_time("14h") == (14, 0)
    assert parse_time("14:30") == (14, 30)


def test_complete_booking_flow():
    bot = SalonBot()
    assert "Tabela de serviços" in bot.respond(10, "oi")
    service_response = bot.respond(10, "quero um alongameto")
    assert service_response == "Qual é o seu nome?"
    assert bot.respond(10, "Ana") == "Qual dia você deseja?"
    assert bot.respond(10, "01/12/2026") == "Qual horário você prefere?"
    assert "Confira seu pedido" in bot.respond(10, "14h")
    confirmation = bot.respond(10, "sim")
    assert "Vou verificar a disponibilidade" in confirmation
    booking = bot.take_confirmed_booking(10)
    assert booking is not None
    assert booking["service"].name == "Alongamento"
    assert booking["customer_name"] == "Ana"
    assert booking["appointment_date"] == "2026-12-01"
    assert booking["appointment_time"] == "14:00"


def test_unknown_message_does_not_invent_service():
    bot = SalonBot()
    response = bot.respond(11, "quero uma coisa diferente")
    assert response == "Não consegui identificar o serviço."


def test_new_booking_without_start_and_service_in_name_step():
    bot = SalonBot()
    bot.respond(12, "blindagem")
    assert bot.respond(12, "blindagem") == "Qual é o seu nome?"
    assert bot.respond(12, "Bia") == "Qual dia você deseja?"


def test_informational_answer_does_not_start_booking():
    bot = SalonBot()
    assert bot.respond(13, "quais serviços vocês oferecem?").startswith("💅 *Tabela")
    assert bot.respond(13, "quanto custa a blindagem?") == "Blindagem custa *R$ 70,00*."


if __name__ == "__main__":
    test_typo_is_understood()
    test_parsers()
    test_complete_booking_flow()
    test_unknown_message_does_not_invent_service()
    print("Todos os testes passaram.")
