# Verified fact sheet (the generator may ONLY make factual claims that appear here)

Add to this file as you verify more. Each fact has a source. If a fact is not here, the
script must not state it as fact. Numbers that change over time (price, hashrate,
difficulty) must NOT be quoted as current unless you add a dated, sourced line.

## Bitcoin mining basics (stable)
- Bitcoin miners compete to add the next block of transactions to the blockchain; the winner earns the block reward (subsidy + fees). Source: https://bitcoin.org/en/developer-guide#mining
- Mining uses repeated SHA-256 hashing: miners search for a block header hash below a network target. Source: https://bitcoin.org/bitcoin.pdf
- The protocol targets one block roughly every 10 minutes on average. Source: https://bitcoin.org/bitcoin.pdf
- Difficulty is recalculated every 2,016 blocks (about two weeks) to keep block time near 10 minutes. Source: https://bitcoin.org/en/developer-guide#mining
- The block subsidy halves every 210,000 blocks (about every four years). It became 3.125 BTC at the April 2024 halving. Source: https://help.blockstream.com/education/glossary/halving
- Bitcoin's supply is capped at 21 million coins. Source: https://bitcoin.org/bitcoin.pdf
- Hashrate is the number of hash attempts per second: 1 TH/s = one trillion hashes per second.
- Mining efficiency is measured in joules per terahash (J/TH), equivalent to watts per TH/s (W/TH). Lower is more efficient.
- Electricity is typically a miner's largest ongoing cost, so efficiency and power price decide whether mining is profitable.
- A single miner finding a block is a matter of probability: your chance per block is your share of the total network hashrate. Pools smooth payouts by sharing rewards in proportion to work contributed.
- Specialised chips called ASICs are far more efficient at SHA-256 than GPUs or CPUs; GPU mining Bitcoin is not practical today.
- Mining rewards are paid in BTC but costs (electricity, hosting) are paid in fiat, so profitability moves with the BTC price. Returns are never guaranteed.

## GoMining (third-party description; confirm on gomining.com before stating current numbers)
- GoMining sells "digital miners": NFTs that represent a share of hashrate hosted in GoMining's data centres, measured in TH/s with an efficiency in W/TH. Source: https://forklog.com/en/what-is-a-digital-miner-and-how-can-you-mine-bitcoin-with-nfts/
- Owners are credited daily bitcoin rewards, minus a maintenance charge that covers electricity and service costs. Source: same Forklog article.
- Digital miners are not redeemable for bitcoin; owners earn rewards, they do not hold the underlying hardware. Source: same Forklog article.
- Rewards and maintenance fees vary with the BTC price, network difficulty and hashrate, so net results vary and can be low or negative. Source: same article (projections depend on price and difficulty).
- NEVER state: specific current prices, ROI numbers, guaranteed or "typical" earnings, or any claim about the creator's own results unless provided in config under `personal_results`.

## Proof of work (stable)
- Finding a valid block is computationally hard, but other nodes can check a block's proof of work cheaply. Source: https://bitcoin.org/bitcoin.pdf

## Blocks and validation (stable; added 18 Oct 2026, from developer.bitcoin.org and the whitepaper)
- Each block stores the hash of the previous block's header, which links blocks into a chain. Source: https://developer.bitcoin.org/devguide/block_chain.html
- Only the 80-byte block header is hashed for proof of work; the merkle root of the block's transactions is stored in the header. Source: https://developer.bitcoin.org/devguide/block_chain.html
- The block header has an easy-to-modify nonce field, so miners can change it to try new hashes. Source: https://developer.bitcoin.org/devguide/block_chain.html
- Each full node independently validates blocks using the same consensus rules. Source: https://developer.bitcoin.org/devguide/block_chain.html
- Nodes accept a block only if all transactions in it are valid and not already spent. Source: https://bitcoin.org/bitcoin.pdf (section 5, Network)
- The first transaction in a block is a special transaction that starts a new coin; transaction fees are added to the block's incentive value. Source: https://bitcoin.org/bitcoin.pdf (section 6, Incentive)
- At each 2,016-block adjustment, difficulty can rise by as much as 300% or fall by as much as 75%. Source: https://developer.bitcoin.org/devguide/block_chain.html (Proof Of Work)
- Proof of work means a block's header hash must not exceed a certain value; new blocks are only added if their hash meets the expected difficulty. Source: https://developer.bitcoin.org/devguide/block_chain.html
