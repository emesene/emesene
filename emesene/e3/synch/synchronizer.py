from synchronizers import emesenesynch

SYNCHLIST={

    "emesene":emesenesynch.emesenesynch,

}

def get_synchronizer(session_type):
    sessions = SYNCHLIST.keys()

    if session_type == "emesene":
        return SYNCHLIST[session_type]()
