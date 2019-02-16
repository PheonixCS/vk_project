# helper for vk video api
import logging


log = logging.getLogger('services.vk.videos')


def get_all_group_videos(api, group_id, count=None):
    max_count = 200  # read api docs
    videos = []

    if count:
        pass
    else:
        resp = api.video.get(owner_id=f'-{group_id}', count=max_count)

        if resp and isinstance(resp, dict):
            in_group_count = resp['count']
            videos.extend(resp['items'])

            if in_group_count > max_count:
                for offset in range(max_count, in_group_count+1, max_count):
                    resp = api.video.get(owner_id=f'-{group_id}', count=max_count, offset=offset)
                    if resp and isinstance(resp, dict):
                        videos.extend(resp['items'])
    return videos

