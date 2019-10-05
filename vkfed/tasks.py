import asyncio

from sanic.log import logger
from aiovk import TokenSession, API
from aiovk.longpoll import BotsLongPoll

from pubgate.db import User
from pubgate.activity import Create
from pubgate.contrib.parsers import process_tags


async def run_vk_bot(app):

    session = TokenSession(access_token='')
    active_bots = await User.find(filter={"details.vkbot.enable": True})
    api = API(session)

    # for bot in active_bots.objects:
    lp = BotsLongPoll(api, mode=2, group_id=187260572)  # default wait=25
    result = await lp.wait()
    result



    bot_swarm = []
    active_bots = await User.find(filter={"details.vkbot.enable": True})
    for bot in active_bots:
        bot_unit = {
            "bot": bot,
            "groups": []
        }
        for group_id,  params in bot["details"]["tgbot"]["groups"]:
            session = TokenSession(access_token=params["access_token"])
            lp = BotsLongPoll(session, mode=2, group_id=group_id)
            # TODO handle last updates on restart
            # if "ts" in params:
            #     lp.ts = params["ts"]
            bot_unit['groups'].append(lp)
        bot_swarm.append(bot_unit)

    while True:
        for bot_unit in bot_swarm:
            for group in bot_unit['groups']:

                result = await group.wait()

                content = result.text
                published = result.date.replace(microsecond=0).isoformat() + "Z"

                attachment = []
                if result.photo:
                    attachment = [{
                        "type": "Document",
                        "mediaType": "image/jpeg",
                        "url": f'{app.base_url}/media/{photo_id}',
                        "name": "null"
                    }]

                    # process tags
                    extra_tag_list = []
                    if bot["details"]["vkbot"]["tags"]:
                        extra_tag_list.extend(bot["details"]["vkbot"]["tags"])
                    content, footer_tags, object_tags = process_tags(extra_tag_list, content)
                    body = f"{content}{footer_tags}"

                    activity = Create(bot, {
                        "type": "Create",
                        "cc": [],
                        "published": published,
                        "object": {
                            "type": "Note",
                            "summary": None,
                            "sensitive": False,
                            "content": body,
                            "published": published,
                            "attachment": attachment,
                            "tag": object_tags
                        }
                    })
                    await activity.save(tg_sent=True)
                    await activity.deliver()
                    logger.info(f"vkontakte entry '{result.id}' of {bot.name} federating")

        await asyncio.sleep(app.config.VK_POLLING_TIMEOUT)
