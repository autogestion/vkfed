## PubGate Vkontakte -> ActivityPub bridge
Extension for [PubGate](https://github.com/autogestion/pubgate), federates posts from Vkontakte public group wall
              
Requires PubGate >= 0.2.19
## Deploy
Create Vkontakte public group and create access token
###### Install Docker + Docker Compose
#### Shell
```
git clone https://github.com/autogestion/pubgate.git
cp -r config/extensions_sample_conf.cfg config/conf.cfg
```
##### Edit config/conf.cfg to change setup of your instance, next values should be added
```
EXTENSIONS = [..., "vkfed"]
VK_POLLING_TIMEOUT = 3
```
This will create bridge skeleton. To establish connection(s), setup PubGate AP account(s).
Account could be created on deploy by adding next value to config/conf.cfg or later via API (described below)
```
USER_ON_DEPLOY = """{
    "username": "user",
    "password": "pass",                                 
    "profile": {
        "type": "Service",                                                  
        "name": "VkFed",
        "summary": "Broadcast from Vkontakte",
        "icon": {
            "type": "Image",
            "mediaType": "image/png",
            "url": "https://cdn1.iconfinder.com/data/icons/blockchain-8/48/icon0008_decentralize-512.png"
        }
    },
    "details": {
        "vkbot": {
            "groups": [{"<group_id>": {"access_token: "<access_token>"}}],                                    
            "enable": true,
            "tags": ["vkontakte", "bridge"]                              
        }
    }
}"""
```
More on user configuration
 - profile -  contains information which will represent bridge in Fediverse
 - details.tgbot.groups - should be updated with targeted Vkontakte group(s)
 - details.tgbot.tags - tags which will be auto-added to every post, could be []

##### Edit requirements/extensions.txt by adding next row
```
git+https://github.com/autogestion/vkfed.git
```

Then, instance could be started
```
domain=put-your-domain-here.com docker-compose up -d
```

### Usage

- To get updates from Vkontakte groups just follow PubGate account from any other AP account

#### Bots Creation via API
```
/user  POST
```
payload 
```
Same as used for USER_ON_DEPLOY value, triple quotes should be stripped
```
If register by invite enabled, "invite": "<invite_code_from_config/conf.cfg>" should be added to payload

##### Restart app after adding new bot or updating old one

#### Disable/Update bot
```
/<username>  PATCH   (auth required)
```
payload
```
{
    "details": {
        "tgbot": {
            "groups": [{"<group_id>": {"access_token: "<access_token>"}}],       #change to update group's list
            "enable": false,                                                     #"enable": true to re-enable
            "tags": ["vkontakte", "bridge"]                              
        }
    }
}
```
