#!/usr/bin/env python

import asmmetadata
import asmyoutube
import argparse
import datetime
import dateutil.parser
import pytz

# Include events from the previous 4 months. Should not include the previous
# event.
MIN_AGE = datetime.timedelta(days=-1)
MAX_AGE = datetime.timedelta(days=120)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile")
    asmyoutube.add_auth_args(parser)
    args = parser.parse_args()
    yt_service = asmyoutube.get_authenticated_service(args)
    entry_data = asmmetadata.parse_file(open(args.datafile, "r"))

    known_video_ids = set(
        [asmmetadata.get_clean_youtube_id(x) for x in filter(
            lambda x: "youtube" in x, entry_data.entries)])

    # Retrieve the contentDetails part of the channel resource for the
    # authenticated user's channel.
    channels_response = yt_service.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

    finished = False
    for channel in channels_response["items"]:
        uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        playlistitems_list_request = yt_service.playlistItems().list(
            playlistId=uploads_list_id,
            part="snippet,status",
            maxResults=50
        )
        for _ in range(10):
            playlistitems_list_response = playlistitems_list_request.execute()

            # Print information about each video.
            for playlist_item in playlistitems_list_response["items"]:
                video_id = playlist_item["snippet"]["resourceId"]["videoId"]
                if video_id in known_video_ids:
                    continue
                status = playlist_item["status"]["privacyStatus"]
                if status != "public":
                    continue
                published_at = dateutil.parser.parse(
                    playlist_item["snippet"]["publishedAt"])
                if now - published_at < MIN_AGE:
                    continue
                if now - published_at > MAX_AGE:
                    finished = True
                    break

                title = playlist_item["snippet"]["title"]
                description = playlist_item["snippet"]["description"]
                description = description.strip()
                if len(description) > 0:
                    description = description.replace(u"\n\n", u"</p><p>")
                    description = description.replace(u"\n", u"<br/>")
                    description = u"|description:%s" % description

                outline = u"title:%s|youtube:%s%s|author:AssemblyTV" % (
                    title, video_id, description)
                print(outline)

            playlistitems_list_request = yt_service.playlistItems().list_next(
                playlistitems_list_request, playlistitems_list_response)
            if finished:
                break
        if finished:
            break
