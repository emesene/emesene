# -*- coding: utf-8 -*-
import Queue
import random

import e3
import gobject
import time

import logging
log = logging.getLogger('dummy.Worker')

class Worker(e3.Worker):
    '''dummy Worker implementation to make it easy to test emesene'''

    def __init__(self, app_name, session, proxy, use_http=False):
        '''class constructor'''
        e3.Worker.__init__(self, app_name, session)
        self.session = session

    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''
        while True:
            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == e3.Action.ACTION_QUIT:
                    log.debug('closing thread')
                    self.session.logger.quit()
                    self.session.signals.quit()
                    break

                self._process_action(action)
            except Queue.Empty:
                pass

    def _fill_contact_list(self):
        """
        method to fill the contact list with something
        """
        self._add_contact('dx@emesene.org', 'XD', e3.status.ONLINE, '', False)
        self._add_contact('roger@emesene.org', 'r0x0r', e3.status.ONLINE,
                '', False)
        self._add_contact('boyska@emesene.org', 'boyska', e3.status.ONLINE,
                '', True)
        self._add_contact('pochu@emesene.org', '<3 debian', e3.status.BUSY,
                '', False)
        self._add_contact('cloud@emesene.org', 'nube', e3.status.BUSY,
                '', False)
        self._add_contact('otacon@emesene.org', 'Otacon', e3.status.BUSY,
                '', True)
        self._add_contact('federico@emesene.org', 'federico..', e3.status.AWAY,
                'he loves guiness', False)
        self._add_contact('respawner@emesene.org', 'Respawner', e3.status.AWAY,
                '', False)
        self._add_contact('mohrtutchy@emesene.org', 'moh..', e3.status.AWAY,
                'one love', True)
        self._add_contact('nassty@emesene.org', 'nassto', e3.status.IDLE,
                '', False)
        self._add_contact('j0hn@emesene.org', 'juan', e3.status.IDLE, '', False)
        self._add_contact('c0n0@emesene.org', 'conoconocono', e3.status.IDLE,
                '', True)
        self._add_contact('warlo@emesene.org', 'warlo', e3.status.OFFLINE,
                '', False)
        self._add_contact('wariano@emesene.org', 'wariano', e3.status.OFFLINE,
                '', False)
        self._add_contact('Faith_Nahn@emesene.org', 'Gtk styler',
                e3.status.BUSY, '', False)
        self._add_contact('you@emesene.org', 'I\'m on emesene code!',
                e3.status.OFFLINE, '', True)

        self._add_contact('one@hotmail.com', '- [b][c=48]Pαrκ¡[/c=30][/b]',
                e3.status.BUSY, '', False)
        self._add_contact('two@hotmail.com',
                '[c=46]-๑๑test_test๑๑-[/c=2]', e3.status.BUSY, '', False)
        self._add_contact('three@hotmail.com',
                '[c=29]•°o.Orandom εïз stuff O.o°•[/c=36]·$28',
                e3.status.BUSY, '', False)
        self._add_contact('four@hotmail.com',
                '[c=48][b]hy[/b][/c=11] ·#·$3,3\'_·$#fcfcfc,#fcfcfc\'_·$4,4\'_·0·$28',
                e3.status.BUSY, '', False)
        self._add_contact('five@hotmail.com',
                '·&·#·$9X.|̲̅·$10X·$9̲̅·$10x·$9̲̅·$10x·$9̲̅·$10x·$9̲̅·$10x·$9̲̅|·$10·#',
                e3.status.BUSY, '', False)
        self._add_contact('six@hotmail.com', '[c=46][u][b]xafd! [/b][/u][/c]',
                e3.status.BUSY, '', False)
        self._add_contact('seven@hotmail.com',
                '[c=5]((_...sdsdf..._))..)_<(_))(°.°)(...][/c=48][u][/u]',
                e3.status.BUSY, '', False)
        self._add_contact('eight@hotmail.com',
                '[i][B][C=12]☆[/C=0][C=0]☆[/C=12][c=12]☆[/c=0] (W) [C=12]Bellamezz[/c=49] (F) [c=0]☆[/c=0][c=12]☆[/c=12][c=0]☆[/c=0][/B][/i]',
                e3.status.BUSY, '', False)
        self._add_contact('nine@hotmail.com',
                '[b](*) ... [c=12]Ricky[/c=33] ...(*)[/b]',
                e3.status.BUSY, '', False)
        self._add_contact('ten@hotmail.com',
                '<:o)[c=yellow]Yellow:DYellow[/c][c=red]Red[c=blue]Blue:)Blue[c=green]Green[/c][/c][/c]',
                e3.status.BUSY, '', False)
        self._add_contact('eleven@hotmail.com',
                '·$,32·$59«·$,41·$50«·$,50·$41«·$,59·$32«·$,66·$23«·$32,1« :: nube ::»·$,66·$23»·$,59·$32»·$,50·$41»·$,41·$50»·$,32·$59»·0 ·$0',
                e3.status.BUSY, '', False)
        self._add_contact('twelve@hotmail.com',
                '·$4Red·$11Aqua·$6,8PurpleOnYellow·$14GrayOnYellow·0Black·$9Lime',
                e3.status.BUSY, '', False)
        self._add_contact('thirteen@hotmail.com',
                '[c=7][b][I am][/c=yellow][/b][c=70][/c=89][c=89] so [A]wesome that [I] only use invalid tags [/c]',
                e3.status.BUSY, '', False)
        self._add_contact('fourteen@hotmail.com',
                '\')")&apos;&quot;:)(H);)&quot;&apos;")\')',
                e3.status.BUSY, '', False)
        self._add_contact('fifteen@hotmail.com',
                '1:)2;)3\')4\')5;)6:)7',
                e3.status.BUSY, '', False)
        self._add_contact('sixteen@hotmail.com',
                '[C=80][i][b][I][/b]Single I[/i][/c=30][b][/C]Single /C[/B]',
                e3.status.BUSY, '', False)

        self._add_group('ninjas')
        self._add_group('pirätes')
        self._add_group('lulz')
        self._add_group('code quiz ninjas')
        self._add_group('empty')
        self._add_group('strange nicks')

        self._add_contact_to_group('you@emesene.org', 'pirätes')
        self._add_contact_to_group('boyska@emesene.org', 'pirätes')
        self._add_contact_to_group('j0hn@emesene.org', 'pirätes')
        self._add_contact_to_group('c0n0@emesene.org', 'pirätes')
        self._add_contact_to_group('nassty@emesene.org', 'lulz')
        self._add_contact_to_group('warlo@emesene.org', 'lulz')
        self._add_contact_to_group('you@emesene.org', 'lulz')
        self._add_contact_to_group('cloud@emesene.org', 'lulz')
        self._add_contact_to_group('dx@emesene.org', 'ninjas')
        self._add_contact_to_group('roger@emesene.org', 'ninjas')
        self._add_contact_to_group('c0n0@emesene.org', 'ninjas')
        self._add_contact_to_group('boyska@emesene.org', 'ninjas')
        self._add_contact_to_group('Faith_Nahn@emesene.org', 'code quiz ninjas')

        self._add_contact_to_group('one@hotmail.com', 'strange nicks')
        self._add_contact_to_group('two@hotmail.com', 'strange nicks')
        self._add_contact_to_group('three@hotmail.com', 'strange nicks')
        self._add_contact_to_group('four@hotmail.com', 'strange nicks')
        self._add_contact_to_group('five@hotmail.com', 'strange nicks')
        self._add_contact_to_group('six@hotmail.com', 'strange nicks')
        self._add_contact_to_group('seven@hotmail.com', 'strange nicks')
        self._add_contact_to_group('eight@hotmail.com', 'strange nicks')
        self._add_contact_to_group('nine@hotmail.com', 'strange nicks')
        self._add_contact_to_group('ten@hotmail.com', 'strange nicks')
        self._add_contact_to_group('eleven@hotmail.com', 'strange nicks')
        self._add_contact_to_group('twelve@hotmail.com', 'strange nicks')
        self._add_contact_to_group('thirteen@hotmail.com', 'strange nicks')
        self._add_contact_to_group('fourteen@hotmail.com', 'strange nicks')
        self._add_contact_to_group('fifteen@hotmail.com', 'strange nicks')
        self._add_contact_to_group('sixteen@hotmail.com', 'strange nicks')

        #test pending contact dialog
        self._add_pending_contacts()

    def _add_pending_contacts(self):
        tmp_cont = e3.base.Contact("test1@test.com", 1,
            "test1", "test1nick",
            e3.status.BUSY, '',
            True)
        self.session.contacts.pending["test1@test.com"] = tmp_cont

        tmp_cont = e3.base.Contact("test2@test.com", 2,
            "test2", "test2nick",
            e3.status.ONLINE, '',
            True)
        self.session.contacts.pending["test2@test.com"] = tmp_cont

    def _late_contact_add(self):
        '''this simulates adding a contact after we show the contactlist'''
        tmp_cont = e3.base.Contact("testlate1@test.com", 1,
            "testlate1", "testlate1nick",
            e3.status.BUSY, '',
            True)
        self.session.contacts.pending["testlate1@test.com"] = tmp_cont
        self.session.contact_added_you()
        return False

    def _return_message(self, cid, account, message):
        ''' Method to return a message after some timeout '''
        self.session.conv_message(cid, account, message)
        message.account = account
        e3.Logger.log_message(self.session, None, message, False)
        return False

    def _add_contact(self, mail, nick, status_, alias, blocked):
        """
        method to add a contact to the contact list
        """
        self.session.contacts.contacts[mail] = e3.Contact(mail, mail,
            nick, '...', status_, alias, blocked)

    def _add_group(self, name):
        """
        method to add a group to the contact list
        """
        self.session.groups[name] = e3.Group(name, name)

    def _add_contact_to_group(self, account, group):
        """
        method to add a contact to a group
        """
        self.session.groups[group].contacts.append(account)
        self.session.contacts.contacts[account].groups.append(group)

    # action handlers
    def _handle_action_add_contact(self, account):
        '''handle Action.ACTION_ADD_CONTACT
        '''
        self.session.contact_add_succeed(account)

    def _handle_action_add_group(self, name):
        '''handle Action.ACTION_ADD_GROUP
        '''
        self.session.group_add_succeed(name)

    def _handle_action_add_to_group(self, account, gid):
        '''handle Action.ACTION_ADD_TO_GROUP
        '''
        self.session.group_add_contact_succeed(gid, account)

    def _handle_action_block_contact(self, account):
        '''handle Action.ACTION_BLOCK_CONTACT
        '''
        self.session.contact_block_succeed(account)

    def _handle_action_unblock_contact(self, account):
        '''handle Action.ACTION_UNBLOCK_CONTACT
        '''
        self.session.contact_unblock_succeed(account)

    def _handle_action_change_status(self, status_):
        '''handle Action.ACTION_CHANGE_STATUS
        '''
        self.session.account.status = status_
        self.session.contacts.me.status = status_
        self.session.status_change_succeed(status_)

    def _handle_action_login(self, account, password, status_):
        '''handle Action.ACTION_LOGIN
        '''
        self.session.login_succeed()
        self.session.nick_change_succeed('dummy nick is dummy')
        self._fill_contact_list()
        self.session.contact_list_ready()
        gobject.timeout_add_seconds(4, self._late_contact_add)

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT
        '''

    def _handle_action_move_to_group(self, account, src_gid, dest_gid):
        '''handle Action.ACTION_MOVE_TO_GROUP
        '''
        self.session.contact_move_succeed(account, src_gid, dest_gid)

    def _handle_action_remove_contact(self, account):
        '''handle Action.ACTION_REMOVE_CONTACT
        '''
        self.session.contact_remove_succeed(account)

    def _handle_action_reject_contact(self, account):
        '''handle Action.ACTION_REJECT_CONTACT
        '''
        self.session.contact_reject_succeed(account)

    def _handle_action_remove_from_group(self, account, gid):
        '''handle Action.ACTION_REMOVE_FROM_GROUP
        '''
        self.session.group_remove_contact_succeed(gid, account)

    def _handle_action_remove_group(self, gid):
        '''handle Action.ACTION_REMOVE_GROUP
        '''
        self.session.group_remove_succeed(gid)

    def _handle_action_rename_group(self, gid, name):
        '''handle Action.ACTION_RENAME_GROUP
        '''
        self.session.group_rename_succeed(gid, name)

    def _handle_action_set_contact_alias(self, account, alias):
        '''handle Action.ACTION_SET_CONTACT_ALIAS
        '''
        self.session.contact_alias_succeed(account)

    def _handle_action_set_message(self, message):
        '''handle Action.ACTION_SET_MESSAGE
        '''
        self.session.message_change_succeed(message)

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK
        '''
        self.session.nick_change_succeed(nick)

    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE
        '''
        self.session.contacts.me.picture = picture_name
        self.session.picture_change_succeed(self.session.account.account,
                picture_name)

    def _handle_action_new_conversation(self, account, cid):
        '''handle Action.ACTION_NEW_CONVERSATION
        '''
        pass

    def _handle_action_close_conversation(self, cid):
        '''handle Action.ACTION_CLOSE_CONVERSATION
        '''
        pass

    def _handle_action_send_message(self, cid, message):
        '''handle Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a Message object
        '''
        self.session.conv_message_send_succeed(cid, message)
        account = random.choice(self.session.contacts.contacts.keys())
        e3.Logger.log_message(self.session, [account], message, True)
        gobject.timeout_add_seconds(1, self._return_message, cid, account, message)

    # p2p handlers

    def _handle_action_p2p_invite(self, cid, pid, dest, type_, identifier):
        '''handle Action.ACTION_P2P_INVITE,
         cid is the conversation id
         pid is the p2p session id, both are numbers that identify the
            conversation and the session respectively, time.time() is
            recommended to be used.
         dest is the destination account
         type_ is one of the e3.Transfer.TYPE_* constants
         identifier is the data that is needed to be sent for the invitation
        '''
        pass

    def _handle_action_p2p_accept(self, pid):
        '''handle Action.ACTION_P2P_ACCEPT'''
        pass

    def _handle_action_p2p_cancel(self, pid):
        '''handle Action.ACTION_P2P_CANCEL'''
        pass
