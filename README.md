# Security_Papers_Crawling
## Introduction
In this repo, we realize a crawler to crawl papers in S&P/CCS/USENIX Security/NDSS for reading papers in the security field according to the keywords given.

在本仓库，我们实现了一个根据给定关键词来爬取安全四大会论文的爬虫。

## Motivation
To our best knowledge, among existing crawlers in github, none has realized crawling papers according to the keywords, which makes screening papers still time-consuming.

我没找到现有可以实现根据关键词爬取论文的爬虫，就很烦，就自己实现一个。

## Method
We use new bing to help us code.

我用new bing辅助写的爬虫

## Implement
python *_Crawling [-C --conference] [-F --save_folder] [-K --keywords]

necessary arguments:

**-C, --conference**:      which conference you want to crawl

optional arguments:

**-F, --save_floder**:     where papers downloaded, default: paper/

**-K, --keywords**:        keywords you want papers include, default: None

## Limitation
- Sensitive to Conference
- Sensitive to Web Layout
- Keywords only support the list of single word, like [membership, adversarial] (will support like [membership inference, adversarial attack] in the future)

## Version
- 0.1 For CCS2022 only
