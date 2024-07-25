# script for auto verifying all `op-contracts/v2.0.0-beta.2` predeploy contracts

This script is used for verifying all predeployed contracts defined in [addresses.go](https://github.com/ethereum-optimism/optimism/blob/op-contracts/v2.0.0-beta.2/op-service/predeploys/addresses.go) in `optimism` repo, including two parts:

- All predeploy contracts with address like `0x420000...` which reside in `optimism` repo, both proxy and implementation are verified.
- All thrid-party contracts used by optimism, refer to `https://specs.optimism.io/protocol/preinstalls.html`

## usage example
```shell
$ make compile
$ python verify.py \
  --chainId 7560 \
  --rpcUrl https://cyber.alt.technology \
  --browserApiUrl https://cyberscan.co/api \
  --browserUrl https://cyberscan.co \
  --proxyOwner 0x299D82fb870e5c0A9a81ff906837Fe617E9dFcAd
```
