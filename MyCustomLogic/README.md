# Installation

1. Run `deploy_locally.sh`.
2. Open Anki, modify the add-on's config, make sure the value of `azure_subscription_key` is set, here is an example:

```json
{
    "azure_subscription_key": "abc"
}
```

You can also put the file directly inside `my_custom_logic/user_files/config.json`. Notice that you may need to create `user_files` and `config.json` manually.