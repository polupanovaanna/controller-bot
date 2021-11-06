from botapitamtam import BotHandler

bot = BotHandler('')

greeting_text = "Здравствуйте!/n Я бот для авторов каналов, для начала работы добавьте меня в свой канал."

def main():
    while True:
        upd = bot.get_updates()  # получаем внутреннее представление сообщения (контента) отправленного боту (сформированного ботом)
        # тут можно вставить любые действия которые должны выполняться во время ожидания события
        if upd: # основной код, для примера представлен эхо-бот
            chat_id = bot.get_chat_id(upd)
            text = bot.get_text(upd)
            if bot.get_update_type(upd) == "bot_started":
                bot.send_message(greeting_text, chat_id)
            bot.send_message(text, chat_id)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()