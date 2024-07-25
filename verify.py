import argparse
import subprocess
import sys

op_proxied_contracts = {
    "0x4200000000000000000000000000000000000016": "L2ToL1MessagePasser",
    "0x4200000000000000000000000000000000000002": "DeployerWhitelist",
    "0x4200000000000000000000000000000000000007": "L2CrossDomainMessenger",
    "0x4200000000000000000000000000000000000010": "L2StandardBridge",
    "0x4200000000000000000000000000000000000011": "SequencerFeeVault",
    "0x4200000000000000000000000000000000000012": "OptimismMintableERC20Factory",
    "0x4200000000000000000000000000000000000013": "L1BlockNumber",
    "0x420000000000000000000000000000000000000F": "GasPriceOracle",
    "0x4200000000000000000000000000000000000015": "L1Block",
    "0x4200000000000000000000000000000000000000": "LegacyMessagePasser",
    "0x4200000000000000000000000000000000000014": "L2ERC721Bridge",
    "0x4200000000000000000000000000000000000017": "OptimismMintableERC721Factory",
    "0x4200000000000000000000000000000000000018": "ProxyAdmin",
    "0x4200000000000000000000000000000000000019": "BaseFeeVault",
    "0x420000000000000000000000000000000000001a": "L1FeeVault",
    "0x4200000000000000000000000000000000000020": "SchemaRegistry",
    "0x4200000000000000000000000000000000000021": "EAS",
}


def predeploy_to_code_namespace(addr: str) -> str:
    """
    https://github.com/ethereum-optimism/optimism/blob/363c5d7f4fb14180a0e2a28cc948fe2146f03dce/packages/contracts-bedrock/src/libraries/Predeploys.sol#L143
    """
    return f"0x{int(addr, 16) & 0xffff | int('0xc0D3C0d3C0d3C0D3c0d3C0d3c0D3C0d3c0d30000', 16):x}"


class Chain:
    chainId: int
    rpcUrl: str
    browserApiUrl: str
    browserUrl: str
    proxyOwner: str

    def __init__(self, chain_id: int, rpc_url: str, browser_api_url: str, browser_url: str, proxy_owner: str):
        self.chainId = chain_id
        self.rpcUrl = rpc_url
        self.browserApiUrl = browser_api_url
        self.browserUrl = browser_url
        self.proxyOwner = proxy_owner


def add_custom_chain(hardhat_config_ts_path: str, chain: Chain):
    template_path = f"{hardhat_config_ts_path}/hardhat.config.ts.template"
    output_path = f"{hardhat_config_ts_path}/hardhat.config.ts"

    with open(template_path, 'r') as f:
        template = f.read()

        template = template.replace('{{ chainId }}', str(chain.chainId))
        template = template.replace('{{ rpcURL }}', chain.rpcUrl)
        template = template.replace('{{ apiURL }}', chain.browserApiUrl)
        template = template.replace('{{ browserURL }}', chain.browserUrl)

    with open(output_path, 'w') as f:
        f.write(template)


def hardhat_verify(repo_path: str, chain: Chain, addresses: [str]):
    add_custom_chain(repo_path, chain)

    for addr in addresses:
        print(f"Verifying {addr} in {repo_path}")
        subprocess.run(f"cd {repo_path} && npx hardhat verify --network custom {addr}", shell=True)


def forge_verify(chain: Chain, path: str, details: [dict]):
    for detail in details:
        addr = detail["addr"]
        contract = detail["contract"]
        compiler_version = detail.get("compiler_version", None)
        n_optimizations = detail.get("n_optimizations", None)
        constructor = detail.get("constructor", None)

        forge_verify_cmd = f"forge verify-contract {addr} {contract} --verifier blockscout --verifier-url {chain.browserApiUrl} --chain-id {chain.chainId} --watch --skip-is-verified-check"
        if compiler_version:
            forge_verify_cmd += f" --compiler-version {compiler_version}"
        if n_optimizations:
            forge_verify_cmd += f" --num-of-optimizations {n_optimizations}"
        # TODO: constructor arg may not be proxyOwner
        if constructor:
            forge_verify_cmd += f" --constructor-args $(cast abi-encode '{constructor}' {chain.proxyOwner})"

        subprocess.run(f"cd {path} && {forge_verify_cmd}", shell=True)


def main(chain: Chain):
    hardhat_projects = [
        {
            "path": "./account-abstraction",
            "addr": ["0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789", "0x7fc98430eaedbb6070b35b39d798725049088348"]
        },
        {
            "path": "./account-abstraction-v0.7.0",
            "addr": ["0x0000000071727De22E5E9d8BAf0edAc6f37da032", "0xEFC2c1444eBCC4Db75e7613d20C6a62fF67A167C"]
        },
        {
            "path": "./safe-smart-account",
            "addr": ["0x69f4D1788e39c87893C980c06EdF4b7f686e2938", "0xfb1bffC9d739B8D520DaF37dF666da4C687191EA",
                     "0x998739BFdAAdde7C933B942a68053933098f9EDa", "0xA1dabEF33b3B82c7814B6D82A79e50F4AC44102B"]
        },
        {
            "path": "./create2deployer",
            "addr": ["0x13b0D85CcB8bf860b6b79AF3029fCA081AE9beF2"]
        }
    ]
    for item in hardhat_projects:
        hardhat_verify(item["path"], chain, item["addr"])

    # multicall
    forge_verify(chain, "./multicall", [
        {
            "addr": "0xcA11bde05977b3631167028862bE2a173976CA11",
            "contract": "./src/Multicall3.sol:Multicall3"
        }
    ])

    # permit2
    forge_verify(chain, './permit2', [
        {
            "addr": "0x000000000022D473030F116dDEE9F6B43aC78BA3",
            "contract": "./src/Permit2.sol:Permit2",
        }
    ])

    # op contracts
    contracts_bedrock_path = "./optimism/packages/contracts-bedrock"
    op_contracts = [
        {
            "addr": "0x4200000000000000000000000000000000000042",
            "contract": "src/governance/GovernanceToken.sol:GovernanceToken",
        },
        {
            "addr": "0x4200000000000000000000000000000000000006",
            "contract": "src/L2/WETH.sol:WETH",
        }
    ]
    # proxies
    op_contracts += [
        {
            "addr": addr,
            "contract": "src/universal/Proxy.sol:Proxy",
            "constructor": "constructor(address)",
        } for addr, name in op_proxied_contracts.items()
    ]
    # implementations
    op_contracts += [
        {
            "addr": predeploy_to_code_namespace(addr),
            "contract": name,
            "compiler_version": "v0.8.15+commit.e14f2714" if name == "ProxyAdmin" else None
        } for addr, name in op_proxied_contracts.items()
    ]

    forge_verify(chain, contracts_bedrock_path, op_contracts)


def cli():
    parser = argparse.ArgumentParser(description='Contract verify')
    parser.add_argument('--chainId', type=int, help='chain id')
    parser.add_argument('--rpcUrl', type=str, help='rpc url')
    parser.add_argument('--browserApiUrl', type=str, help='browser api url')
    parser.add_argument('--browserUrl', type=str, help='browser url')
    parser.add_argument('--proxyOwner', type=str, help='proxy owner address')

    args = parser.parse_args()
    # check required args
    if not all([args.chainId, args.rpcUrl, args.browserApiUrl, args.browserUrl, args.proxyOwner]):
        parser.print_help()
        return
    chain = Chain(args.chainId, args.rpcUrl, args.browserApiUrl, args.browserUrl, args.proxyOwner)

    main(chain)


if __name__ == '__main__':
    cli()
