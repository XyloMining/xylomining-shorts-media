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

## GoMining referral bonuses for new users (added 30 Oct 2026; terms can change, say "can get" and never promise)
- GoMining's referral page (screenshot supplied by the creator, 30 Oct 2026) lists for a referred friend: 5% bonus TH on their first miner within 30 days after registration, up to 25 TH; a TH bonus for the first card spending within 90 days after registration; and 1 month of Platinum+ within 30 days after registration. Source: https://gomining.com/blog/gomining-partner (confirms 5% extra mining power on the first miner, a free month of Platinum+ VIP and a card-spending mining-power bonus; the 25 TH cap and time windows come from the creator's screenshot of the referral page).
- GoMining states referral rewards are a promo mechanic whose sizes and terms may change, and that products and features are subject to eligibility, its terms and regional availability. Source: https://gomining.com/blog/gomining-partner

## Block header, target, supply and coinbase (added 10 Nov 2026; fetched and read this session)
- The block header is a compact 80-byte bundle: version (4 bytes), previous block hash (32), merkle root (32), timestamp (4), nBits (4) and nonce (4). Source: https://help.blockstream.com/education/glossary/block-header
- The version field tells nodes which consensus rules the miner applied; the previous block hash links a block to its predecessor; the merkle root is a single hash that commits to every transaction in the block. Source: https://help.blockstream.com/education/glossary/block-header
- The nBits field encodes the difficulty target the header's hash must be at or below; the nonce is a 32-bit counter miners increment while searching. Source: https://help.blockstream.com/education/glossary/block-header
- Each header is hashed twice (double SHA-256) and the result must be at or below the target. Source: https://help.blockstream.com/education/glossary/block-header
- Nodes reject block headers whose timestamps are more than two hours ahead of their clocks or earlier than the median of the last 11 blocks. Source: https://help.blockstream.com/education/glossary/block-header
- The target is a 256-bit number shared by all Bitcoin clients; a block's hash must be lower than or equal to it, and the lower the target, the harder it is to generate a block. Source: https://en.bitcoin.it/wiki/Target
- Every 2016 blocks (two weeks at one block per 10 minutes) clients compare actual time with the two-week goal and adjust the target; a single retarget never changes the target by more than a factor of 4 either way. Source: https://en.bitcoin.it/wiki/Target
- The block subsidy was 50 BTC, then 25, 12.5, 6.25 and 3.125 BTC after the April 2024 halving (block 840,000). Earlier halvings: block 210,000 (Nov 2012), 420,000 (Jul 2016), 630,000 (May 2020). Source: https://www.learnbitcoin.com/rabbit-hole/supply
- The first 210,000-block era issued 10,500,000 BTC, about half of the 21 million cap. Source: https://www.learnbitcoin.com/rabbit-hole/supply
- Because the subsidy rounds down at satoshi precision, the real ceiling is 20,999,999.9769 BTC, slightly under 21 million. Source: https://www.learnbitcoin.com/rabbit-hole/supply
- One satoshi is the smallest unit: 1/100,000,000 of a bitcoin. Source: https://www.learnbitcoin.com/rabbit-hole/supply
- The subsidy is expected to reach zero around the year 2140; after that miners are paid only by transaction fees. Source: https://www.learnbitcoin.com/rabbit-hole/supply
- The 50 BTC reward of the genesis block (3 January 2009) was never spendable. Source: https://www.learnbitcoin.com/rabbit-hole/supply and https://www.spark.money/glossary/coinbase-transaction
- In November 2010 two blocks (91,842 and 91,880) overwrote earlier coinbase transactions, making another 100 BTC unspendable. Source: https://www.learnbitcoin.com/rabbit-hole/supply
- The miner of block 501,726 (December 2017) claimed none of its 12.5 BTC subsidy. Source: https://www.learnbitcoin.com/rabbit-hole/supply
- The coinbase transaction is the first transaction in every block; it creates the new coins and collects fees, and spends no previous output. Source: https://www.spark.money/glossary/coinbase-transaction
- Coinbase outputs cannot be spent until they have 100 confirmations. Source: https://www.spark.money/glossary/coinbase-transaction
- A miner may claim less than subsidy plus fees; the unclaimed amount is destroyed. Source: https://www.spark.money/glossary/coinbase-transaction
