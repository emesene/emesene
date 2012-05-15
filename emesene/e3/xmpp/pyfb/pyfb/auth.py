"""
    $Id: auth.py

    This file is a mapper for the specified permissions in
    http://developers.facebook.com/docs/reference/api/permissions/
"""

#User related permissions

USER_ABOUT_ME = "user_about_me"
USER_ACTIVITIES = "user_activities"
USER_BIRTHDAY = "user_birthday"
USER_CHECKINS = "user_checkins"
USER_EDUCATION_HISTORY = "user_education_history"
USER_EVENTS = "user_events"
USER_GROUPS = "user_groups"
USER_HOMETOWN = "user_hometown"
USER_INTERESTS = "user_interests"
USER_LIKES = "user_likes"
USER_LOCATION = "user_location"
USER_NOTES = "user_notes"
USER_ONLINE_PRESENCE = "user_online_presence"
USER_PHOTO_VIDEO_TAGS = "user_photo_video_tags"
USER_PHOTOS = "user_photos"
USER_RELATIONSHIPS = "user_relationships"
USER_RELATIONSHIP_DETAILS = "user_relationship_details"
USER_RELIGION_POLITICS = "user_religion_politics"
USER_STATUS = "user_status"
USER_VIDEOS = "user_videos"
USER_WEBSITE = "user_website"
USER_WORK_HISTORY = "user_work_history"
USER_EMAIL = "email"
USER_READ_FRIENDLISTS = "read_friendlists"
USER_READ_INSIGHTS = "read_insights"
USER_READ_MAILBOX = "read_mailbox"
USER_READ_REQUESTS = "read_requests"
USER_READ_STREAM = "read_stream"
USER_XMPP_LOGIN = "xmpp_login"
USER_ADS_MANAGEMENT = "ads_management"

vars = locals().copy()
USER_ALL_PERMISSIONS = [value for key, value in vars.iteritems() if key.startswith("USER_")]

#Friends related permissions

FRIENDS_ABOUT_ME = "friends_about_me"
FRIENDS_ACTIVITIES = "friends_activities"
FRIENDS_BIRTHDAY = "friends_birthday"
FRIENDS_CHECKINS = "friends_checkins"
FRIENDS_EDUCATION_HISTORY = "friends_education_history"
FRIENDS_EVENTS = "friends_events"
FRIENDS_GROUPS = "friends_groups"
FRIENDS_HOMETOWN = "friends_hometown"
FRIENDS_INTERESTS = "friends_interests"
FRIENDS_LIKES = "friends_likes"
FRIENDS_LOCATION = "friends_location"
FRIENDS_NOTES = "friends_notes"
FRIENDS_ONLINE_PRESENCE = "friends_online_presence"
FRIENDS_PHOTO_VIDEO_TAGS = "friends_photo_video_tags"
FRIENDS_PHOTOS = "friends_photos"
FRIENDS_RELATIONSHIPS = "friends_relationships"
FRIENDS_RELATIONSHIP_DETAILS = "friends_relationship_details"
FRIENDS_RELIGION_POLITICS = "friends_religion_politics"
FRIENDS_STATUS = "friends_status"
FRIENDS_VIDEOS = "friends_videos"
FRIENDS_WEBSITE = "friends_website"
FRIENDS_WORK_HISTORY = "friends_work_history"

vars = locals().copy()
FRIENDS_ALL_PERMISSIONS = [value for key, value in vars.iteritems() if key.startswith("FRIENDS_")]

#Write related permissions

WRITE_PUBLISH_STREAM = "publish_stream"
WRITE_CREATE_EVENT = "create_event"
WRITE_RSVP_EVENT = "rsvp_event"
WRITE_SMS = "sms"
WRITE_OFFLINE_ACCESS = "offline_access"
WRITE_PUBLISH_CHECKINS = "publish_checkins"
WRITE_MANAGE_FRIENDLISTS = "manage_friendlists"

vars = locals().copy()
WRITE_ALL_PERMISSIONS = [value for key, value in vars.iteritems() if key.startswith("WRITE_")]

#Page related permissions

PAGE_MANAGE_PAGES = "manage_pages"

vars = locals().copy()
PAGE_ALL_PERMISSIONS = [value for key, value in vars.iteritems() if key.startswith("PAGE_")]

#All permisssions
ALL_PERMISSIONS = USER_ALL_PERMISSIONS + FRIENDS_ALL_PERMISSIONS + WRITE_ALL_PERMISSIONS + PAGE_ALL_PERMISSIONS

