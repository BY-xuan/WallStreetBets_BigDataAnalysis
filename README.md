# WallStreetBets Stock Research Posts Prediction

***

More than ever, stock trading has become democratized to retail investors. One of the most popular platforms for discussion is a subreddit called WallStreetBets. Unlike professional investors, retail investors have very limited time to conduct their own research as they usually have a separate career. In this project, we aim to further democratize stock trading by using prediction and filtering on research so that every regular investor has the opportunity to quickly access quality information and analysis.

The dataset we will use are the reddit posts categorized as “DD” (Due Diligence), which are stock research on WallStreetBets. We will collect this data by using the Reddit API and use classification to separate the serious research posts from the meme posts by tokenizing the content with Bag-of-words method and by applying Naive-Bayes method. We will then check the stock growth of a stock corresponding to a given serious post repeatedly, in a given time interval, and use this data to make a prediction on future research posts of this subreddit.

***

## I. Introduction

## II. Materials and Methods
For this project, we will use two datasets. 
The first dataset is the subReddit post/submission from Reddit, which is extracted by using "praw" API and pushshift API. The Reddit dataset has 9 columns of data: title,score,upvote_ratio,author,text,URL,created(timestamp), comments and link flair text (tags). Except for upvote_ratio and created(timestamp), all data are textual data. There are many ways to analyze textual data; the Naive-Bayes method can be used to build a Reddit-post classifier. Naive Bayes methods are a set of supervised learning algorithms based on applying Bayes' theorem with the "naive" assumption of conditional independence between every pair of features given the value of the class variable. To build the Naive-Bayes classifier, we need to extract features from the textual data from these posts. We can first start with the posts' tags to identify them (tags such as DD, MEME, YOLO, Discussion). However, the tags are not reliable because there is a chance that the author is posting a meme with the "DD" tag. The other way to extract features is to tokenize all the English words in the text using bag-of-words model or n-gram model. Count their frequencies and find the same words in other posts. Moreover, We can use an NLP library to classify the English words based on the synonyms. Once we have our features, we can split the posts into significant posts and less significant posts.

The second dataset is the stock market data from iexfinance. This dataset includes the quote, stats, financials, cash-flow, volumes of a specific ticker. However, we are interested in the ticker's time-series data, which is the quote and trade volumes in a given time interval, to measure the effects of a wallstreatbets post on a stock. With the features built in the first step and the associated stock data, we want to find similar posts and predict that stock's "growth" that is mentioned in a new significant post. We can build linear regression model to predict the growth. The key challenge for linear regression model is the data type. We have to extract a number data from the textual data. Instead of making a sentiment analysis, we would like to analyze the content of a post. To do so, we can use the bag-of-words model or n-gram model again plus Principal component analysis to find most significant words and sentences.

Matthew Pan (40135588)<br>
Ling Zhi Mo (40024810)
