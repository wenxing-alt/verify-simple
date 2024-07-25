all: prepare

ensure-forge:
	@which forge || (echo "Please install forge: https://book.getfoundry.sh/getting-started/installation" && exit 1)

ensure-node:
	@which node || (echo "Please install node: https://nodejs.org/en/download/" && exit 1)

ensure-yarn:
	@which yarn || (echo "Please install yarn: https://classic.yarnpkg.com/en/docs/install" && exit 1)

prepare: ensure-forge ensure-node ensure-yarn
	git submodule update --init --recursive

compile: prepare
	cd account-abstraction && yarn && npx hardhat compile
	cd account-abstraction-v0.7.0 && yarn && npx hardhat compile
	cd safe-smart-account && yarn && npx hardhat compile
	cd create2deployer && npm i && npx hardhat compile
	cd permit2 && forge install && forge build
	cd optimism/packages/contracts-bedrock && forge build
	cd multicall && forge install && forge build

