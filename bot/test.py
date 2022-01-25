import unittest
from bot_info import tester_bot_token_1, tester_bot_token_2, tester_bot_token_3, tested_bot_id, bot_chat_id, bot_chat_id_2
from botapitamtam import *
import requests
import main, text
import threading


class TestBotMethods(unittest.TestCase):
    def test_bot_added_no_rights(self):
        test_chat = test_chat_1
        tester_bot_1.add_members(test_chat, tested_bot_id)
        tester_bot_1.send_message("/set_channel", bot_chat_id)
        update = tester_bot_1.get_updates(timeout=10)
        self.assertEqual(tester_bot_1.get_chat_id(update), test_chat)
        self.assertEqual("Бот пока что не состоит ни в одном канале.", tester_bot_1.get_text(update))

    def test_bot_creates_poll(self):
        test_chat = test_chat_2
        tester_bot_2.send_message("/set_channel", bot_chat_id)
        upd = tester_bot_2.get_updates()
        self.assertEqual(tester_bot_2.get_text(upd), "Выберите канал, с которым вы ходите работать:\n1. Test_channel4\n2. Test_channel2")
        self.assertEqual(tester_bot_2.get_chat_id(upd), bot_chat_id)
        tester_bot_2.send_message("1", bot_chat_id)
        upd = tester_bot_2.get_updates()
        self.assertEqual(tester_bot_2.get_text(upd), "Канал был успешно установлен!")
        tester_bot_2.send_message("/create_poll", bot_chat_id)
        upd = tester_bot_2.get_updates(2)
        self.assertEqual(tester_bot_2.get_text(upd[1]), "Укажите заголовок опроса")
        tester_bot_2.send_message("test_poll", bot_chat_id)
        upd = tester_bot_2.get_updates()
        self.assertEqual(tester_bot_2.get_text(upd), "Укажите число вариантов ответа")
        tester_bot_2.send_message("12e", bot_chat_id)
        upd = tester_bot_2.get_updates()
        self.assertEqual(tester_bot_2.get_text(upd), "Неправильно введено число. Попробуйте еще раз.")

        tester_bot_2.send_message("0", bot_chat_id)
        upd = tester_bot_2.get_updates()
        self.assertEqual(tester_bot_2.get_text(upd), "Вы ввели число вне допустимого диапазона. Попробуйте еще раз.")

        tester_bot_2.send_message("1000000000", bot_chat_id)
        upd = tester_bot_2.get_updates()
        self.assertEqual(tester_bot_2.get_text(upd), "Вы ввели число вне допустимого диапазона. Попробуйте еще раз.")
        tester_bot_2.send_message("10", bot_chat_id)
        for i in range(10):
            upd = tester_bot_2.get_updates()
            self.assertEqual(tester_bot_2.get_text(upd), f"Введите вариант ответа №{i+1}")
            upd = tester_bot_2.get_updates(timeout=0.1)
            self.assertEqual(upd, None)
            tester_bot_2.send_message(f"{i}", bot_chat_id)
        upd = tester_bot_2.get_updates()

        self.assertEqual(tester_bot_2.get_text(upd), "test_poll")
        self.assertEqual(len(tester_bot_2.get_attachments(upd)[0]["payload"]["buttons"]), 10)
        print(tester_bot_2.get_attachments(upd))
        upd = tester_bot_2.get_updates(timeout=5)
        self.assertEqual(upd, None)
        tester_bot_2.send_message("/exit", bot_chat_id)


    def test_multiple_requests_different_channels(self):
        thread_bot_2 = threading.Thread(target=self.test_bot_creates_poll)
        thread_bot_2.start()
        tester_bot_3.send_message("/set_channel", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
        self.assertEqual(tester_bot_3.get_text(upd), "Выберите канал, с которым вы ходите работать:\n1. Test_channel4\n2. Test_channel3")
        self.assertEqual(tester_bot_3.get_chat_id(upd), bot_chat_id_2)
        tester_bot_3.send_message("1", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
        self.assertEqual(tester_bot_3.get_text(upd), "Канал был успешно установлен!")
        tester_bot_3.send_message("/create_poll", bot_chat_id_2)
        upd = tester_bot_3.get_updates(2)
        self.assertEqual(tester_bot_2.get_text(upd[1]), "Укажите заголовок опроса")
        tester_bot_3.send_message("test_poll_bot_3", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
        self.assertEqual(tester_bot_3.get_text(upd), "Укажите число вариантов ответа")
        for i in range(15):
            tester_bot_3.send_message(f"{i*3+1}e", bot_chat_id_2)
            upd = tester_bot_3.get_updates()
            self.assertEqual(tester_bot_3.get_text(upd), "Неправильно введено число. Попробуйте еще раз.")

        tester_bot_3.send_message("0", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
        self.assertEqual(tester_bot_3.get_text(upd), "Вы ввели число вне допустимого диапазона. Попробуйте еще раз.")

        tester_bot_3.send_message("1000000000", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
        self.assertEqual(tester_bot_3.get_text(upd), "Вы ввели число вне допустимого диапазона. Попробуйте еще раз.")
        tester_bot_3.send_message("5", bot_chat_id_2)
        for i in range(5):
            upd = tester_bot_3.get_updates()
            self.assertEqual(tester_bot_3.get_text(upd), f"Введите вариант ответа №{i + 1}")
            upd = tester_bot_3.get_updates(timeout=0.1)
            self.assertEqual(upd, None)
            tester_bot_3.send_message(f"{i}", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
        self.assertEqual(tester_bot_3.get_text(upd), "test_poll_bot_3")
        self.assertEqual(len(tester_bot_3.get_attachments(upd)[0]["payload"]["buttons"]), 5)
        upd = tester_bot_3.get_updates(timeout=5)
        self.assertEqual(upd, None)
        tester_bot_3.send_message("/exit", bot_chat_id_2)
        thread_bot_2.join()


    def test_create_poll_one_channel(self):
        first = threading.Thread(target=test_create_poll_no_asserts, args=(tester_bot_3, "first"))
        second = threading.Thread(target=test_create_poll_no_asserts, args=(tester_bot_2, "second"))
        first.start()
        time.sleep(5)
        second.start()
        first.join()
        second.join()
        upd = tester_bot_3.get_updates(2)
        self.assert_(tester_bot_3.get_text(upd[0]) == "first" and tester_bot_3.get_text(upd[1]) == "second")

def test_create_poll_no_asserts(tester_bot_3, poll_name):
    tester_bot_3.send_message("/set_channel", bot_chat_id_2)
    upd = tester_bot_3.get_updates()
    tester_bot_3.send_message("2", bot_chat_id_2)
    upd = tester_bot_3.get_updates()
    tester_bot_3.send_message("/create_poll", bot_chat_id_2)
    upd = tester_bot_3.get_updates(2)
    tester_bot_3.send_message(f"{poll_name}", bot_chat_id_2)
    upd = tester_bot_3.get_updates()
    for i in range(15):
        tester_bot_3.send_message(f"{i * 3 + 1}e", bot_chat_id_2)
        upd = tester_bot_3.get_updates()
    tester_bot_3.send_message("0", bot_chat_id_2)
    upd = tester_bot_3.get_updates()
    tester_bot_3.send_message("1000000000", bot_chat_id_2)
    upd = tester_bot_3.get_updates()
    tester_bot_3.send_message("5", bot_chat_id_2)
    for i in range(5):
        upd = tester_bot_3.get_updates()
        upd = tester_bot_3.get_updates(timeout=0.1)
        tester_bot_3.send_message(f"{i}", bot_chat_id_2)


tester_bot_1 = BotHandler(tester_bot_token_1)
tester_bot_2 = BotHandler(tester_bot_token_2)
tester_bot_3 = BotHandler(tester_bot_token_3)
test_chat_1 = [i["chat_id"] for i in tester_bot_1.get_all_chats()["chats"]][0]
print([i["chat_id"] for i in tester_bot_2.get_all_chats()["chats"]])
test_chat_2 = [i["chat_id"] for i in tester_bot_2.get_all_chats()["chats"]][1]
test_chat_4 = [i["chat_id"] for i in tester_bot_2.get_all_chats()["chats"]][2]

test_chat_3 = [i["chat_id"] for i in tester_bot_3.get_all_chats()["chats"]][1]
test_chat_4 = [i["chat_id"] for i in tester_bot_3.get_all_chats()["chats"]][2]
tester_bot_3.send_message("hello", test_chat_4)
if __name__ == '__main__':
    unittest.main()
