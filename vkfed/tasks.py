import asyncio

from sanic.log import logger
from aiovk import TokenSession, API
from aiovk.longpoll import BotsLongPoll

from pubgate.db import User
from pubgate.activity import Create
from pubgate.contrib.parsers import process_tags


async def run_vk_bot(app):

    bot_swarm = []
    active_bots = await User.find(filter={"details.vkbot.enable": True})
    for bot in active_bots.objects:
        bot_unit = {
            "bot": bot,
            "groups": []
        }
        for group in bot["details"]["vkbot"]["groups"]:
            session = TokenSession(access_token=group["access_token"])
            lp = BotsLongPoll(session, mode=2, group_id=group["group_id"])
            # TODO handle last updates on restart
            # if "ts" in params:
            #     lp.ts = params["ts"]
            bot_unit['groups'].append(lp)
        bot_swarm.append(bot_unit)

    while True:
        for bot_unit in bot_swarm:
            bot = bot_unit["bot"]

            for group in bot_unit['groups']:
                result = await group.wait()
                updates = result['updates']
                for update in updates:
                    if update["type"] == 'wall_post_new':
                        post = update["object"]

                        attachments = []
                        if post.get('attachments'):
                            for row_attachment in post['attachments']:
                                if row_attachment['type'] == 'photo':
                                    attachments.append({
                                        "type": "Document",
                                        "mediaType": "image/jpeg",
                                        "url": row_attachment['photo']["photo_807"],
                                        "name": "null"
                                    })

                        # process tags
                        extra_tag_list = []
                        if bot["details"]["vkbot"]["tags"]:
                            extra_tag_list.extend(bot["details"]["vkbot"]["tags"])
                        content, footer_tags, object_tags = process_tags(
                            extra_tag_list, post['text']
                        )
                        body = f"{content}{footer_tags}"

                        activity = Create(bot, {
                            "type": "Create",
                            "cc": [],
                            "object": {
                                "type": "Note",
                                "summary": None,
                                "sensitive": False,
                                "content": body,
                                "attachment": attachments,
                                "tag": object_tags
                            }
                        })
                        await activity.save(tg_sent=True)
                        await activity.deliver()
                        logger.info(f"vkontakte entry '{post['id']}' of {bot.name} federating")

        await asyncio.sleep(app.config.VK_POLLING_TIMEOUT)
