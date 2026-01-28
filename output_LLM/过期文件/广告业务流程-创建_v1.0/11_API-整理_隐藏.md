# API-整理[隐藏]  

> 来源: 广告业务流程-创建 / API-整理  

### API-整理 [隐藏]  

| 排序 | 广告类型 | 名称 | path | 中文 | 版本 | 出现 | 优先级 | 备注（请看批注较重要） |
|---|---|---|---|---|---|---|---|---|
| 1 | SP | ListSponsoredProductsCampaigns | /sp/campaigns/list | SP广告活动 | V3 | 广告创建 | 1 |  |
| 2 | SP | ListSponsoredProductsAdGroups | /sp/adGroups/list | SP广告组 | V3 | 广告创建 | 3 |  |
| 3 | SP | ListSponsoredProductsProductAds | /sp/productAds/list | SP广告组推广产品 | V3 | 广告创建 | 4 |  |
| 4 | SP | ListSponsoredProductsTargetingClauses | /sp/targets/list | SP广告组商品投放 | V3 | 广告创建 | 5 |  |
| 5 | SP | ListSponsoredProductsNegativeTargetingClauses | /sp/negativeTargets/list | SP广告组否定商品投放 | V3 | 广告创建 | 7 |  |
| 6 | SP | ListSponsoredProductsKeywords | /sp/keywords/list | SP广告组关键词投放 | V3 | 广告创建 | 6 |  |
| 7 | SP | ListSponsoredProductsNegativeKeywords | /sp/negativeKeywords/list | SP广告组否定关键词投放 | V3 | 广告创建 | 8 |  |
| 8 | SP | ListSponsoredProductsCampaignNegativeTargetingClauses | /sp/campaignNegativeTargets/list | SP广告活动否定商品投放 | V3 | 广告运行 | 9 |  |
| 9 | SP | ListSponsoredProductsCampaignNegativeKeywords | /sp/campaignNegativeKeywords/list | SP广告活动否定关键词投放 | V3 | 广告运行 | 10 |  |
| 10 | SP | Budget usage API for SP campaigns | /sp/campaigns/budget/usage | SP广告活动使用预算 | V3 | 广告运行 | 2 |  |
| 11 | SP | Get bid recommendations for ad groups | /sp/targets/bid/recommendations | SP广告组投放推荐竞价 | V3 | 广告创建 | 11 |  |
| 12 | SP | Get keyword recommendations | /sp/targets/keywords/recommendations | SP广告组投放推荐关键词 | V3 | 广告创建 | 12 |  |
| 13 | SB | List campaigns | /sb/v4/campaigns | SB广告活动 | V4 | 广告创建 |  |  |
| 14 | SB | List ad groups | /sb/v4/adGroups/list | SB广告组 | V4 | 广告创建 |  |  |
| 15 | SB | List ads | /sb/v4/ads/list | SB广告组广告格式&广告素材（已发布） | V4 | 广告创建 |  | 初步判断为成功发布的SB广告信息 |
| 16 | SB | listTargets | /sb/targets/list | SB广告组商品投放 | V3 | 广告创建 |  | /sb/targets/{targetId}，初步核对字段一致 |
| 17 | SB | Gets a list of product negative targets associated with the client identifier passed in the authorization header, filtered by specified criteria | /sb/negativeTargets/list | SB广告组否定商品投放 | V3 | 广告创建 |  | /sb/negativeTargets/{negativeTargetId}，初步核对，/sb/negativeTargets/{negativeTargetId}无bid（bid否定投放不需要该值），其他字段一致 |
| 18 | SB | Gets an array of keywords, filtered by optional criteria. | /sb/keywords | SB广告组关键词投放 | V3 | 广告创建 |  | /sb/keywords/{keywordId}，初步核对字段一致 |
| 19 | SB | sbListThemes | /sb/themes/list | SB广告组投放主题 | V3 | 广告创建 |  |  |
| 20 | SB | Gets an array of negative keywords, filtered by optional criteria. | /sb/negativeKeywords | SB广告组否定关键词投放 | V3 | 广告创建 |  | /sb/negativeKeywords/{keywordId}，初步核对字段一致 |
| 21 | SB | List ad creatives | /sb/ads/creatives/list | SB广告组广告格式&广告素材（创建审核） | V4 | 广告创建 |  | 数据基本同/sb/v4/ads/list，广告创建状态：已提交供审核、待翻译、待审核、已通过审核、已拒绝、已发布 |
| 22 | SB | Get budget usage | /sb/campaigns/budget/usage | SB广告活动使用预算 | V4 | 广告运行 |  |  |
| 23 | SB | getBidsRecommendations | /sb/recommendations/bids | SB广告组投放推荐竞价 | V3 | 广告创建 |  |  |
| 24 | SD | Gets a list of campaigns with extended fields | /sd/campaigns/extended | SD广告活动 | 无版本目录 | 广告创建 |  | /sd/campaigns与/sd/campaigns/{campaignId}初步核对字段一致，对比/sd/campaigns/extended缺少servingStatus、creationDate、lastUpdatedDate，/sd/campaigns/extended无deliveryProfile（该字段不重要）；/sd/campaigns/extended与/sd/campaigns/extended/{campaignId}初步核对字段一致 |
| 25 | SD | Gets a list of ad groups with extended fields | /sd/adGroups/extended | SD广告组 | 无版本目录 | 广告创建 |  | /sd/adGroups与/sd/adGroups/{adGroupId}初步核对字段一致，对比/sd/adGroups/extended缺少servingStatus、creationDate、lastUpdatedDate；/sd/adGroups/extended与/sd/adGroups/extended/{adGroupId}初步核对字段一致 |
| 26 | SD | Gets a list of product ads with extended fields. | /sd/productAds/extended | SD广告组推广产品 | 无版本目录 | 广告创建 |  | /sd/productAds与/sd/productAds/{adId}初步核对字段一致，对比/sd/productAds/extended缺少servingStatus、creationDate、lastUpdatedDate；/sd/productAds/extended与/sd/productAds/extended/{adId}初步核对字段一致 |
| 27 | SD | Gets a list of targeting clause objects with extended fields. | /sd/targets/extended | SD广告组投放 | 无版本目录 | 广告创建 |  | /sd/targets与/sd/targets/{targetId}初步核对字段一致，对比/sd/targets/extended缺少servingStatus、creationDate、lastUpdatedDate；/sd/targets/extended与/sd/targets/extended/{targetId}初步核对字段一致 |
| 28 | SD | Gets a list of negative targeting clause objects with extended fields. | /sd/negativeTargets/extended | SD广告组否定投放 | 无版本目录 | 广告创建 |  | /sd/negativeTargets与/sd/negativeTargets/{negativeTargetId}初步核对字段一致，对比/sd/targets/extended缺少servingStatus、creationDate、lastUpdatedDate，多出resolvedExpression； /sd/negativeTargets/extended与/sd/negativeTargets/extended/{negativeTargetId}初步核对字段一致 |
| 29 | SD | Gets a list of creatives | /sd/creatives | SD广告组广告格式&广告素材 | 无版本目录 | 广告创建 |  |  |
| 30 | SD | Budget usage API for SD campaigns | /sd/campaigns/budget/usage | SD广告活动使用预算 | 无版本目录 | 广告运行 |  |  |
| 31 | SD | Returns a set of recommended products and categories to target | /sd/targets/recommendations | SD广告组投放推荐 | 无版本目录 | 广告创建 |  |  |
| 32 | SD | Returns a set of bid recommendations for targeting clauses | /sd/targets/bid/recommendations | SD广告组投放竞价推荐 | 无版本目录 | 广告创建 |  |  |

