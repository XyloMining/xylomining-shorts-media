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

## Overflow bug, pools, mempool, reorgs, energy, hashprice, GoMining fees (added 16 Nov 2026; fetched and read this session)
- On 15 Aug 2010, block 74638 contained a transaction that created 184,467,440,737.09551616 bitcoins for three addresses, because the transaction-checking code did not account for outputs so large they overflowed when summed. Source: https://en.bitcoin.it/wiki/Value_overflow_incident
- A fixed client was released within about five hours; it rejected overflow transactions. The patched chain overtook the bad chain at block 74691 on 16 Aug 2010, and the bad transaction no longer exists on the longest chain. Source: https://en.bitcoin.it/wiki/Value_overflow_incident
- Mining pools split the block reward according to contributed processing power; a share is awarded to a client who presents a valid proof of work. Source: https://en.bitcoin.it/wiki/Pooled_mining
- Pools smooth incentives for lower-performance miners, who get a smaller amount more regularly instead of waiting a very long time for a block. Source: https://en.bitcoin.it/wiki/Pooled_mining
- Solo miners keep the whole block reward and fees but with higher variance; pool miners get smaller, more frequent payments with lower variance. Source: https://developer.bitcoin.org/devguide/mining.html
- With PPS payouts a pool pays a flat amount per share, which moves the risk to the pool operator. Source: https://en.bitcoin.it/wiki/Pooled_mining
- Pools charge fees to cover infrastructure and operational risk; pool fees come out of miners' earnings, and rates differ by pool and payout method, so check your pool's current terms. Source: https://www.viabtc.com/blog/Mining-what-are-mining-pool-fees-ppsppsfppspplns-fee-structures-487
- The mempool is the holding area for transactions that have been broadcast but not yet included in a block; every full node keeps its own mempool, and they are similar but not identical. Source: https://www.learnbitcoin.com/rabbit-hole/mempool
- Miners rank transactions by fee rate (fee divided by size, in sat/vB), because block space is scarce; blocks have roughly 4 million weight units of space. Source: https://www.learnbitcoin.com/rabbit-hole/mempool
- A low-fee transaction is valid but can wait a long time; when a mempool fills up, the lowest fee-rate transactions are dropped. Source: https://www.learnbitcoin.com/rabbit-hole/mempool
- A chain reorganization (reorg) happens when a node finds a different chain with more total work that excludes blocks it had accepted; it is local to each node, and the excluded blocks become orphans. Source: https://en.bitcoin.it/wiki/Chain_Reorganization
- The genesis block is dated 3 Jan 2009; its coinbase carries the text "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks", and its 50 BTC reward is unspendable. Source: https://en.bitcoin.it/wiki/Genesis_block
- The issuance schedule is fixed in advance; blocks that issue more than the rules allow are rejected by the network. Source: https://en.bitcoin.it/wiki/Controlled_supply
- Once new issuance approaches zero, miners are paid only by transaction fees. Source: https://en.bitcoin.it/wiki/Controlled_supply
- ASIC resistance is the (mostly failed) effort to design proof-of-work algorithms that gain little from specialised chips, so mining stays with hobbyists; Scrypt (Litecoin) got ASICs in 2014 and Ethash (Ethereum) by 2018. Bitcoin does not pursue ASIC resistance. Source: https://www.learnbitcoin.com/glossary/asic-resistance
- Cambridge's 2025 report put sustainable energy at 52.4% of Bitcoin mining's energy mix (42.6% renewables, 9.8% nuclear), natural gas at 38.2% and coal at 8.9% (down from 36.6% in 2022). Source: https://www.jbs.cam.ac.uk/2025/cambridge-study-sustainable-energy-rising-in-bitcoin-mining/
- A Bitaxe is an open-source Bitcoin ASIC miner: a single chip on a small board that runs quietly on a desk; a Gamma-class unit is about 1 TH/s at roughly 15 to 21 W. Source: https://www.tftc.io/bitaxe-explained
- The same source says a single Gamma-class device would take roughly 17,000 years on average to find a block solo, expected earnings are effectively zero, and a Bitaxe should not be bought as an income device. Source: https://www.tftc.io/bitaxe-explained
- Warning signs of fraudulent crypto offers per the SEC investor alert: promised or "guaranteed" high returns, complicated jargon, unlicensed sellers, offers that sound too good to be true, unsolicited contact, pressure to act fast, and requests to pay more to withdraw profits. Source: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/investor-alert-watch-out-fraudulent-digital-asset-and-crypto-trading-websites
- A rough planning figure for an ASIC's physical service life is three to five years, not a warranty; its economic life can be much shorter if electricity costs rise, difficulty rises, hashprice falls or newer machines are more efficient. A machine can be online yet economically obsolete. Source: https://www.viabtc.com/en/blog/Insights-how-long-does-an-asic-miner-last-physical-vs-economic-life-in-2026-647
- Hashprice is the expected value of 1 PH/s of hashrate per day; in BTC it depends on block subsidy, transaction fees and network difficulty, and in USD also on the bitcoin price. Source: https://docs.luxor.tech/hashrateindex/hashprice
- One hosting firm argues hashrate tends to follow bitcoin price with a lag of weeks to months, because hardware and facilities take time to build; when hashrate falls, blocks slow down until difficulty adjusts. Source: https://www.simplemining.io/insights/post/the-relationship-between-bitcoin-price-hashrate
- GoMining's docs say it deducts maintenance fees (electricity and equipment service) from the pool reward, and give Net Reward = Pool Reward - (Electricity + Service) x (1 - Discounts). Source: https://docs.gomining.com/en/product/miners/maintenance-fees-and-discounts
- GoMining's docs say paying maintenance with GOMINING tokens can give a discount of up to 20%, VIP status gives a discount that grows with level, and a daily service-button streak adds a small discount; terms can change. Source: https://docs.gomining.com/en/product/miners/maintenance-fees-and-discounts
- GoMining's docs say you can upgrade a miner's computing power (TH) and energy efficiency (W/TH) to maximise net rewards, and that daily BTC rewards are proportional to a miner's power and efficiency. Source: https://docs.gomining.com/en/product/miners
- A hardware wallet is a small dedicated device that stores private keys and signs transactions; the keys are generated inside it and never leave it. Its seed phrase is still the master backup, and anyone who gets that phrase does not need the device. Source: https://www.learnbitcoin.com/glossary/hardware-wallet
- MEV is profit that block producers can extract by including, excluding or reordering pending transactions; the term originally stood for "miner extractable value" and became "maximal extractable value" after Ethereum moved to proof-of-stake. MEV strategies are less lucrative on Bitcoin because it lacks smart contracts. Source: https://www.coindesk.com/learn/what-is-mev-aka-maximal-extractable-value
