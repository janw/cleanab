# CleanAB — Clean A Budget for YNAB

This is re-[inventing](https://github.com/schurig/ynab-bank-importer) [the](https://bitbucket.org/ctheune/ynab-bank-imports/src/default/) [wheel](https://github.com/bank2ynab/bank2ynab). 💁‍♀️

Import FinTS/HBCI transactions (🇩🇪 👋) into [YNAB](https://ynab.com/referral/?ref=DP9o_rOK4sNtCxhD&utm_source=customer_referral) using its API. My rationale for creating this (instead of using an existing solution), was the poor parsing/processing/cleanup of transaction data like payee and memo in other tools. Configuratin is done in YAML and can include an arbitrary amount of replacement definitions that should be applied to the transaction data. See [config.yaml.sample](config.yaml.sample) for example use.

## Running with Docker

Copy [config.yaml.sample](config.yaml.sample) to a location of your chosing, adjust to your setup, and mount it to `/app/config.yaml` in a container:

```bash
docker run -v /path/to/your/config.yaml:/app/config.yaml registry.gitlab.com/janw/cleanab
```
