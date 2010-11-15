import os
import time
import StringIO
import unittest

import e3

e3.Logger.Logger.COMMIT_LIMIT = 0
logger = e3.Logger.LoggerProcess("test")
logger.start()
full_path = os.path.join("test", "base.db")

ME_ACCOUNT = "marianoguerra@emesene.org"
ME_NICK = "marianoguerra"
ME_MESSAGE = "I'm a message"
ME_IMAGE = "image.png"

CLOUD_ACCOUNT = "cloud@emesene.org"

class LoggerTestCase(unittest.TestCase):

    def test_db_created(self):
        self.assertTrue(os.path.exists(full_path))

    def build_me(self):
        return self.build_account("1", ME_ACCOUNT, nick=ME_NICK,
                message=ME_MESSAGE, path=ME_IMAGE)

    def build_cloud(self):
        return self.build_account("2", CLOUD_ACCOUNT,
            nick="nube", message="lol")

    def build_dx(self):
        return self.build_account("3", "dx@emesene.org",
            nick="kiace", message="XD")

    def build_account(self, cid, account="foo@hotmail.com",
            status=e3.status.ONLINE, nick="Foo!", message="oh hai!", path="",
            id_account=None):
        return e3.Logger.Account(cid, id_account, account, status, nick, message, path)

    def test_message(self):
        src = self.build_me()
        dest = self.build_cloud()
        message = "oh hai!!"

        def callback(result):
            self.assertEquals(len(result), 1)
            status, timestamp, payload = result[0]
            self.assertEquals(status, src.status)
            self.assertEquals(payload, message)

        logger.log('message', src.status, message, src, dest)
        logger.get_event(src.account, 'message', 10, callback)
        logger.check(True)

        def test_get_chats():
            def callback(result):
                self.assertTrue(result)
                self.assertEquals(len(result), 1)
                status, timestamp, payload, nick, account = result[0]
                self.assertEquals(status, e3.status.ONLINE)
                self.assertEquals(payload, "oh hai!!")

            logger.get_chats(ME_ACCOUNT, CLOUD_ACCOUNT, 10, callback)
            logger.check(True)

        def test_get_chats_between():
            def callback(result):
                self.assertTrue(result)
                self.assertEquals(len(result), 1)
                status, timestamp, payload, nick, account = result[0]
                self.assertEquals(status, e3.status.ONLINE)
                self.assertEquals(payload, "oh hai!!")

            to_t = time.time() + 100
            from_t = to_t - 1000

            logger.get_chats_between(ME_ACCOUNT, CLOUD_ACCOUNT, from_t, to_t, 10, callback)
            logger.check(True)

        def test_get_sent_messages():
            def callback(result):
                self.assertTrue(result)
                self.assertEquals(len(result), 1)
                timestamp, payload = result[0]
                self.assertEquals(payload, "oh hai!!")

            logger.get_sent_messages(ME_ACCOUNT, CLOUD_ACCOUNT, 10, callback)
            logger.check(True)

        def test_txt_exporter():
            def callback(result):
                out = StringIO.StringIO()
                e3.Logger.save_logs_as_txt(result, out)
                status, timestamp, payload, nick, account = result[0]
                out.seek(0)
                log = out.read()
                self.assertTrue(payload in log)
                self.assertTrue(nick in log)

            logger.get_chats(ME_ACCOUNT, CLOUD_ACCOUNT, 10, callback)
            logger.check(True)

        # do all this tests here to ensure that they are called after the
        # message was created
        test_get_chats()
        test_get_chats_between()
        test_get_sent_messages()
        test_txt_exporter()

    def test_add_contacts(self):
        me = self.build_me()
        cloud = self.build_cloud()

        accounts = {
            CLOUD_ACCOUNT: e3.Contact(CLOUD_ACCOUNT, cid="2"),
            ME_ACCOUNT: e3.Contact(ME_ACCOUNT, cid="1")
        }

        logger.add_contacts(accounts)
        time.sleep(1)
        self.assertEquals(len(logger.logger.accounts), 2)

    def test_add_groups(self):
        g1 = e3.Group("group 1", "g1")
        g2 = e3.Group("group 2", "g2")

        groups = {
            g1.identifier: g1,
            g2.identifier: g2
        }

        logger.add_groups(groups)
        # add twice to check that they are only added once
        logger.add_groups(groups)
        time.sleep(1)
        self.assertEquals(len(logger.logger.groups), 2)

    def test_logger_already_created_database(self):
        log = e3.Logger.Logger("test")
        self.assertTrue(len(log.accounts) > 0)
        self.assertTrue(len(log.events) > 0)
        log.close()

    def test_get_chats_invalid_src(self):
        def callback(result):
            self.assertFalse(result)

        logger.get_chats("asd", CLOUD_ACCOUNT, 10, callback)
        logger.check(True)


    def test_get_sent_messages_invalid(self):
        def callback(result):
            self.assertFalse(result)

        logger.get_sent_messages("asd", CLOUD_ACCOUNT, 10, callback)
        logger.check(True)

    def test_account_from_contact(self):
        contact = e3.Contact(ME_ACCOUNT, "1", "nick", "message", e3.status.BUSY,
                "alias", cid="1")

        contact.picture = "picture"

        account = e3.Logger.Account.from_contact(contact)

        self.assertEquals(contact.account, account.account)
        self.assertEquals(contact.cid, account.id)
        self.assertEquals(contact.status, account.status)
        self.assertEquals(contact.nick, account.nick)
        self.assertEquals(contact.message, account.message)
        self.assertEquals(contact.picture, account.path)

    def test_get_chats_between_invalid_src(self):
        def callback(result):
            self.assertFalse(result)

        to_t = time.time() + 100
        from_t = to_t - 1000

        logger.get_chats_between("asd", CLOUD_ACCOUNT, from_t, to_t, 10, callback)
        logger.check(True)

    def test_inexistent_handler_error(self):
        old = e3.Logger.log.error

        def new_log_error(msg):
            e3.Logger.log.error = old
            self.assertEquals("invalid action foo on LoggerProcess", msg)

        e3.Logger.log.error = new_log_error

        logger.input.put(('foo', (1, 2, 3)))

    def test_get_nicks(self):
        def callback(result):
            self.assertTrue(result)
            self.assertEquals(len(result), 1)
            self.assertEquals(result[0][2], ME_NICK)

        logger.log('nick change', e3.status.ONLINE, ME_NICK,
            self.build_me())
        logger.get_nicks(ME_ACCOUNT, 10, callback)
        time.sleep(1)
        logger.check()

    def test_get_messages(self):
        def callback(result):
            self.assertTrue(result)
            self.assertEquals(len(result), 1)
            self.assertEquals(result[0][2], ME_MESSAGE)

        logger.log('message change', e3.status.ONLINE, ME_MESSAGE,
            self.build_me())
        logger.get_messages(ME_ACCOUNT, 10, callback)
        logger.check(True)

    def test_account_str(self):
        me = self.build_me()
        self.assertEquals(str(me), "<account '%s'>" % me.account)

    def test_group_str(self):
        group = e3.Logger.Group("g1", "group 1", 1, True)
        self.assertEquals(str(group), "<group '%s'>" % group.name)

    def test_get_images(self):
        def callback(result):
            self.assertTrue(result)
            self.assertEquals(len(result), 1)
            self.assertEquals(result[0][2], ME_IMAGE)

        logger.log('image change', e3.status.ONLINE, ME_IMAGE,
            self.build_me())
        logger.get_images(ME_ACCOUNT, 10, callback)
        logger.check(True)

    def test_get_status(self):
        def callback(result):
            self.assertTrue(result)
            self.assertEquals(len(result), 1)
            self.assertEquals(result[0][2], str(e3.status.ONLINE))

        logger.log('status change', e3.status.ONLINE, str(e3.status.ONLINE),
            self.build_cloud())
        logger.get_status(CLOUD_ACCOUNT, 10, callback)
        logger.check(True)

    def test_get_invalid_event(self):
        def callback(result):
            self.assertEquals(result, None)

        logger.get_event(ME_ACCOUNT, 'asd', 10, callback)
        logger.check(True)

    def test_get_event_invalid_account(self):
        def callback(result):
            self.assertEquals(result, None)

        logger.get_event('asd', 'chat', 10, callback)
        logger.check(True)

    def test_existin_handler_error(self):
        old = e3.Logger.log.error

        def new_log_error(msg):
            e3.Logger.log.error = old
            self.assertTrue("error calling action add_contacts on LoggerProcess: " in msg)

        e3.Logger.log.error = new_log_error

        logger.input.put(('add_contacts', (1, )))

    def test_quit_and_restart(self):
        global logger
        logger.quit()
        time.sleep(1)
        logger = e3.Logger.LoggerProcess("test")
        logger.start()

    def __del__(self):
        logger.quit()
        logger.join()

        if os.path.exists(full_path):
            os.remove(full_path)
