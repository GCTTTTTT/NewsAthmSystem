# 结果还行！！！！！初版完成！！！！
# FIX：3.25 归一化后是乘以100！
# Fix:3.29 mbert+bilstm+SelfAttention版本
import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import BertTokenizer, BertModel, AdamW, get_linear_schedule_with_warmup
import torch.nn as nn
import os


def DateDataProcess_Impl(date_sel):
    import pandas as pd
    import torch
    from transformers import BertTokenizer, BertForSequenceClassification
    from transformers import BertTokenizer, BertModel, AdamW, get_linear_schedule_with_warmup
    import torch.nn as nn
    import os
    # 定义Self-Attention层
    class SelfAttention(nn.Module):
        def __init__(self, hidden_size):
            super(SelfAttention, self).__init__()
            self.hidden_size = hidden_size
            self.projection = nn.Sequential(
                nn.Linear(hidden_size, 64),
                nn.ReLU(True),
                nn.Linear(64, 1)
            )

        def forward(self, encoder_outputs):
            energy = self.projection(encoder_outputs)
            weights = torch.softmax(energy.squeeze(-1), dim=1)
            outputs = (encoder_outputs * weights.unsqueeze(-1)).sum(dim=1)
            return outputs


        # 定义模型
    class NewsClassifier(nn.Module):
        # hidden_size = 128
        def __init__(self, bert_model,num_classes, hidden_size, num_layers=2, bidirectional=True):
            super(NewsClassifier, self).__init__()
            # self.bert = BertModel.from_pretrained('../../bert-base-multilingual-cased')
            self.bert = bert_model # FIX

            # self.lstm = nn.LSTM(input_size=hidden_size, hidden_size=hidden_size, num_layers=num_layers, 
            #                     bidirectional=bidirectional, batch_first=True)
            self.lstm = nn.LSTM(input_size=bert_model.config.hidden_size, hidden_size=hidden_size, num_layers=num_layers, 
                                bidirectional=bidirectional, batch_first=True) # FIX

            self.attention = SelfAttention(hidden_size * (2 if bidirectional else 1))
            self.fc = nn.Linear(hidden_size * (2 if bidirectional else 1), num_classes)

        def forward(self, input_ids, attention_mask):
            outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
            last_hidden_state = outputs.last_hidden_state
            lstm_outputs, _ = self.lstm(last_hidden_state)
            attention_outputs = self.attention(lstm_outputs)
            logits = self.fc(attention_outputs)
            return logits



    # 加载训练好的模型
    model_path = './models/bert-base-multilingual-cased'  ## 可更换
    # modelNew_load_path = './classificationModel/bert-base-multilingual-cased_classification_undersampled_new_epoch_20.pth'  ## 可更换
    # modelNew_load_path = '../NewsAthmTask2Score/classificationModel/bert-base-multilingual-cased_classification_undersampled_new_epoch_20.pth'  ## 可更换
    modelNew_load_path = './classificationModel/best_MultiBert_BiLSTM_SelfAttention_modelFIX_fold_5.pth'  ## 可更换

    model_CLS_name = "mbert_BiLSTM_SelfAttention" ###!!!

    # model = BertForSequenceClassification.from_pretrained(model_path, num_labels=9)
    model = BertModel.from_pretrained(model_path)

    # 加载tokenizer
    tokenizer = BertTokenizer.from_pretrained(model_path)

    # 将模型移动到GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # print(device)
    # model.to(device)



    print(device)
    model.to(device)

    # 设置超参数
    max_length = 512
    hidden_size = 128
    num_classes = 9
    num_layers = 2
    bidirectional = True


    # 加载训练好的模型
    # modelNew_load_path = '../NewsAthmTask2Score/classificationModel/best_MultiBert_BiLSTM_SelfAttention_modelFIX_fold_5.pth'  ## 可更换
    model = NewsClassifier(bert_model = model,num_classes=num_classes, hidden_size=hidden_size, num_layers=num_layers, bidirectional=bidirectional)
    model.load_state_dict(torch.load(modelNew_load_path))
    model.to(device)
    model.eval()

    # 定义类别列表
    # categories = ['খেলাধুলা', 'রাজনীতি', 'বিনোদন', 'অর্থনীতি', 'আইন', 'শিক্ষা', 'বিজ্ঞান', 'লাইফস্টাইল', 'অন্যান্য']
    # categories = ['রাজনীত','লাইফস্টাইল','শিক্ষা','অর্থনীতি','খেলাধুলা','অন্যান্য','বিজ্ঞান','বিনোদন', 'আইন'] # FIX!!!!!!!!!!!!
    
    categories = ['রাজনীতি','লাইফস্টাইল','শিক্ষা','অর্থনীতি','খেলাধুলা','অন্যান্য','বিজ্ঞান','বিনোদন', 'আইন'] # FIX!!!!!!!!!!!!   政治改正

    # [‘政治’、‘生活方式’、‘教育’、‘经济’、‘体育’、‘其他’、‘科学’、‘娱乐’、‘法律’]

    # 定义数据处理函数
    def preprocess_data(text, tokenizer, max_length):
        encoding = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=max_length,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt',
            truncation=True
        )
        return encoding['input_ids'].to(device), encoding['attention_mask'].to(device)

    # 定义预测函数
    def predict(model, input_ids, attention_mask):
        with torch.no_grad():
            outputs = model(input_ids, attention_mask)
            _, preds = torch.max(outputs, dim=1)
        return preds.item(), categories[preds.item()]
        # return preds.item()




    # 读取csv文件
    # data = pd.read_csv('./Data231202-231211/Data231202.csv')  ## 
    # data = pd.read_csv('./datasets/news_20240302_20240311.csv')  ## 对0302-0311这10天进行评估  从数据库爬取（定时任务）--->拿到数据--->根据date筛选
    
    data_file_path = f'./datasets/mbert_BiLSTM_SelfAttention/{date_sel}/news_{date_sel}.csv'
    # data = pd.read_csv('./datasets/news_20240302_20240318.csv')  ## 对0302-0318这进行评估  从数据库爬取（定时任务）--->拿到数据--->根据date筛选
    data = pd.read_csv(data_file_path)  ## 对0302-0318这进行评估  从数据库爬取（定时任务）--->拿到数据--->根据date筛选

    data['pub_time'] = pd.to_datetime(data['pub_time'])

    # date_UNI = '2024-03-12' ###
    date_UNI = date_sel ###

    # 筛选 pub_time 为 '2024-03-02' 的数据
    filtered_data = data[data['pub_time'] == date_UNI]  ## 这个日期是参数！系统端传过来后进行处理 系统传日期---》查询数据库（看是否有缓存。没有的话就现查）---》筛选

    # filtered_data.to_csv("./test0302.csv", index=False)

    # 显示筛选结果
    # print(filtered_data)


    nan_check = filtered_data['body'].isna().sum()
    nan_check_c = filtered_data['category1'].isna().sum()
    print(nan_check)
    print(nan_check_c)

    filtered_data = filtered_data.dropna(subset=['category1','body'])
    nan_check = filtered_data['body'].isna().sum()
    nan_check_c = filtered_data['category1'].isna().sum()
    print(nan_check)
    print(nan_check_c)


    processed_data_file_name = f"./datasets/{model_CLS_name}/news_{date_UNI}_processed_{model_CLS_name}.csv"
    
    # FIX:缓存操作 若已有文件则直接读取 否则才进行预测
    # 判断文件是否存在
    if os.path.exists(processed_data_file_name):
        # 如果文件存在，则直接读取数据
        processed_data = pd.read_csv(processed_data_file_name)
    else:
        # 如果文件不存在，则执行处理数据的函数
        # processed_data = process_data(data)
        # processed_data = process_data(filtered_data)

        # FIX:
        predicted_categories = []
        cnt = 0
        for idx, row in filtered_data.iterrows():
            cnt+=1
            if cnt%200 == 0: 
                print("categoryProcessing")
                print(cnt)
            if row['category1'] not in categories:
                input_ids, attention_mask = preprocess_data(row['body'], tokenizer, max_length)
                pred_id, predicted_category = predict(model, input_ids, attention_mask)
                predicted_categories.append(predicted_category)
                # predicted_categories_id.append(pred_id)
            else:
                predicted_categories.append(row['category1'])
                # predicted_categories_id.append(row['category1'])

        # 将预测后的类别替换原有的category1列
        filtered_data['category1'] = predicted_categories
        processed_data = filtered_data

        # 将处理后的数据保存到文件中
        processed_data.to_csv(processed_data_file_name, index=False)

    print("FINISH!!")





    # conda angle https://github.com/SeanLee97/AnglE/tree/main
    # pip install nltk
    # pip install --upgrade pip
    # pip install spacy==2.3.5
    # pip install bn_core_news_sm-0.1.0.tar.gz
    # pip install matplotlib
    import pandas as pd
    # from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    import torch
    from transformers import AutoModel, AutoTokenizer
    from angle_emb import AnglE

    # yes! 聚类评估！！！可跑 TP, FP, TN, FN 得到RI、Precision、Recall、F1，ARI
    # update:单个成簇的处理
    from itertools import combinations
    from math import comb

    from sklearn.preprocessing import MinMaxScaler

    import networkx as nx
    from collections import defaultdict
    from nltk.tokenize import word_tokenize # 使用NLTK进行分词，根据需要替换为适合孟加拉语的分词方法

    import spacy
    # from gensim.summarization import keywords
    from collections import defaultdict
    import bn_core_news_sm
    from sklearn.preprocessing import MinMaxScaler # 归一化
    import matplotlib.pyplot as plt
    # import pytextrank
    # =======
    # 去除停用词
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    nltk.download('stopwords')


    import string
    # ====================


    # data_ORI = pd.read_csv('./Data231202-231211/Data231202.csv') # 所有子任务都是使用这个
    data_ORI = processed_data

    # 使用angle加载
    # model_id = '../NewsAthmTask2/models/angle-bert-base-uncased-nli-en-v1' ## 可更换
    model_id = './models/angle-bert-base-uncased-nli-en-v1' ## 可更换

    angle = AnglE.from_pretrained(model_id, pooling_strategy='cls_avg').cuda()

    # 加载数据
    data = data_ORI

    # 将日期转换为日期时间格式
    data['pub_time'] = pd.to_datetime(data['pub_time'])

    # 获取唯一日期列表
    dates = data['pub_time'].dt.date.unique()


    # 定义聚类中心更新函数
    def update_cluster_center(cluster):
        cluster_embeddings = angle.encode(cluster, to_numpy=True) # 使用angle加载

        return np.mean(cluster_embeddings, axis=0)

    def get_predicted_clusters(data,threshold):
        # 对于每个日期
        cluster_results = []
        cnt = 0
        for date in dates:
            print(cnt)
            cnt+=1
            # 获取该日期的新闻标题
            news_data = data[data['pub_time'].dt.date == date]['title'].tolist()
            # 获取该日期的新闻正文
            # news_data = data[data['pub_time'].dt.date == date]['body'].tolist() # ByBody

            embeddings = angle.encode(news_data, to_numpy=True) # 使用angle加载

            # 定义当天的簇列表
            daily_clusters = []

            # 对于每个新闻数据
            for i, embedding in enumerate(embeddings):
                # 如果簇列表为空，则新开一个簇
                if not daily_clusters:
                    # daily_clusters.append({'center': embedding, 'members': [news_data[i]]})
                    daily_clusters.append({'center': embedding, 'members': [i],'news':[news_data[i]]}) # 改为存index
                    continue

                # 计算当前数据点与各个簇中心的相似度
                similarities = [cosine_similarity([embedding], [cluster['center']])[0][0] for cluster in daily_clusters]

                # 找到最大相似度及其对应的簇索引
                max_similarity = max(similarities)
                max_index = similarities.index(max_similarity)

                # 如果最大相似度大于阈值，则将当前数据点加入对应簇，并更新簇中心
                if max_similarity > threshold:
                    daily_clusters[max_index]['members'].append(i) # 改为存index
                    daily_clusters[max_index]['news'].append(news_data[i]) # 改为存index
                    daily_clusters[max_index]['center'] = update_cluster_center(daily_clusters[max_index]['news'])
                # 否则新开一个簇
                else:
                    daily_clusters.append({'center': embedding, 'members': [i],'news':[news_data[i]]}) # 改为存index

            # 将当天的簇信息添加到结果列表中
            cluster_results.append({'date': date, 'clusters': daily_clusters})

        predicted_clusters = []
        for cluster in cluster_results[0]['clusters']: # 2023-12-02的簇s
            clus_index = []
            for i in cluster['members']:
                clus_index.append(i)
            predicted_clusters.append(clus_index)
        print(predicted_clusters)

        return predicted_clusters

    # 设置阈值
    threshold = 0.972  ## 可更换
    clusters = get_predicted_clusters(data,threshold)

    # 创建一个字典，键是语料索引，值是对应的簇大小
    index_to_cluster_size = {index: len(cluster) for cluster in clusters for index in cluster}

    # 读取语料文件
    df = data_ORI

    # 新增列clus_news_num，记录每个语料对应的簇的大小
    df['T1_clus_news_num'] = df.index.map(index_to_cluster_size)

    # 根据簇大小进行排序，并添加排名，相同大小的排名相同
    df = df.sort_values(by='T1_clus_news_num', ascending=False)
    df['T1_rank'] = df['T1_clus_news_num'].rank(method='min', ascending=False)

    # 新增列S_scale，为簇大小的归一化结果
    scaler = MinMaxScaler()
    df['T1_S_scale'] = scaler.fit_transform(df[['T1_clus_news_num']])

    # # 新增列S_score，为S_scale的值乘以20
    # df['T1_S_score'] = df['T1_S_scale'] * 20

    # 新增列S_score，为S_scale的值乘以20
    df['T1_S_score'] = df['T1_S_scale'] * 100

    # 新增列index，表示语料原始的坐标
    df['T1_ori_indexFrom0'] = df.index

    # 只保留需要的列，并保存到新的CSV文件
    T1_final_df = df[['id','T1_ori_indexFrom0', 'title', 'body', 'T1_clus_news_num', 'T1_rank','T1_S_scale', 'T1_S_score']]

    # 文件保存处理，若有重名文件，则重命名为_{num}  好像并不需要 每天的是固定的 后续可能直接查询就行
    # num_file_T1 = 1

    # # 检查文件是否存在
    # while os.path.exists(T1_file_name):
    #     T1_file_name = f"./T1ClusterScore/T1_{date_UNI}_result_new_{num_file_T1}.csv"
    #     num_file_T1 += 1

    T1_file_name = f"./T1ClusterScore/{model_CLS_name}/T1_{date_UNI}_{model_CLS_name}_result_new.csv"
    T1_final_df.to_csv(T1_file_name, index=False)
    print("FINISH!")


    # 40个网站的排名以及赋分结果在./T2WebsiteRank/website_Rank_new.csv
    # Data231202-231211/Data231202.csv
    # 读取Data231202-231211/Data231202.csv，其中的website_id为网站id，现在读取./T2WebsiteRank/website_Rank_new.csv，该文件存有website_id对应的S_task_web，现在需要将Data231202.csv中的每个语料对应的website_id对应的S_task_web新增一列进行存储，然后根据S_task_web进行排序，允许并列，新增rank列，将结果中website_id,title,S_task_web,rank存到新的csv文件

    # 读取两个csv文件
    data_df = data_ORI
    # rank_df = pd.read_csv('./T2WebsiteRank/website_Rank_new.csv')
    rank_df = pd.read_csv('./T2WebsiteRank/website_Rank_new_FIX.csv') # FIX


    # 将两个DataFrame合并
    merged_df = pd.merge(data_df, rank_df, on='website_id')

    # 根据S_task_web列进行排序，并添加排名，相同权重的排名相同
    merged_df = merged_df.sort_values(by='T2_S_score', ascending=False)
    merged_df['T2_rank'] = merged_df['T2_S_score'].rank(method='min', ascending=False)

    # 只保留需要的列，并保存到新的CSV文件
    T2_final_df = merged_df[['id','website_id', 'title', 'T2_S_score', 'T2_rank']]

    T2_file_name = f"./T2WebsiteRank/{model_CLS_name}/T2_{date_UNI}_{model_CLS_name}_result_new.csv" ## FIX
    # T2_final_df.to_csv('./T2WebsiteRank/Data231202_scoreResult.csv', index=False)
    T2_final_df.to_csv(T2_file_name, index=False)



    # 读取CSV文件并计算正文长度
    df = data_ORI
    df['body_len'] = df['body'].apply(lambda x: len(str(x).split()))  # 假设每个单词之间用空格分隔

    # 按正文长度进行排序
    df = df.sort_values(by='body_len', ascending=False)

    # 添加排名列
    df['T3_rank'] = df['body_len'].rank(method='min', ascending=False)

    # 计算S_scale并添加列
    max_len = df['body_len'].max()
    min_len = df['body_len'].min()
    df['T3_S_scale'] = (df['body_len'] - min_len) / (max_len - min_len)

    # # 计算body_len_score并添加列
    # df['T3_S_score'] = 20 * df['T3_S_scale']

    # 计算body_len_score并添加列
    df['T3_S_score'] = 100 * df['T3_S_scale'] #FIX

    # 保存结果到新的CSV文件
    T3_file_name_1 = f"./T3BodyLenRank/{model_CLS_name}/T3_{date_UNI}_{model_CLS_name}_result_new_all.csv"
    T3_file_name_2 = f"./T3BodyLenRank/{model_CLS_name}/T3_{date_UNI}_{model_CLS_name}_result_new.csv"

    # output_file = './T3BodyLenRank/Data231202_newDATA_rank_Score_new.csv'  # 替换为你的输出文件路径
    # df.to_csv(output_file, index=False)
    df.to_csv(T3_file_name_1, index=False)


    # 只保留需要的列，并保存到新的CSV文件
    T3_final_df = df[['id','title', 'body_len', 'T3_rank','T3_S_scale', 'T3_S_score']]
    # T3_final_df.to_csv('./T3BodyLenRank/Data231202_T3scoreResult.csv', index=False)
    T3_final_df.to_csv(T3_file_name_2, index=False)

    print("处理完成，并将结果保存到新的CSV文件中。")




    # 加载孟加拉语模型
    nlp = bn_core_news_sm.load()
    # # textrank算法计算权重
    # update 3.9：改进版！！
    def textrank_weighted_word_graph(merged_titles):
        tokens = nlp(merged_titles) # 分词
        print(len(tokens))
        # print(tokens)

        graph = nx.Graph()
        window_size = 80  # 根据需要调整窗口大小

        for i, token in enumerate(tokens):
            for j in range(i+1, min(i+window_size+1, len(tokens))):
                if token != tokens[j]:  # 添加边,避免自环
                    if graph.has_edge(token, tokens[j]):
                        graph[token][tokens[j]]['weight'] += 1 #在添加边时,先检查边是否已经存在。如果边已经存在,则将权重加1;否则,添加一个新边,权重为1。这样可以避免重复添加边。
                    else:
                        graph.add_edge(token, tokens[j], weight=1)

        # 使用NetworkX的PageRank算法计算每个节点（词）的权重
        pagerank_scores = nx.pagerank(graph, weight='weight')

        return pagerank_scores,graph

    # 读取CSV文件并合并所有标题
    df = data_ORI

    merged_titles = ' '.join(title.strip() for title in df['title'])

    # ====================================
    # 获取孟加拉语的停用词列表
    stop_words = set(stopwords.words('bengali'))
    # print(stop_words)

    # 自定义标点符号列表
    custom_punctuation = ['‘', '’']

    # 合并 NLTK 提供的标点符号列表和自定义标点符号列表
    all_punctuation = string.punctuation + ''.join(custom_punctuation)

    print(all_punctuation)
    # 分词# word_tokens = word_tokenize(merged_titles)

    word_tokens = nlp(merged_titles) # 分词
    # word_tokens = merged_titles.split() # 根据空格分词
    token_texts = [token.text.strip() for token in word_tokens] # 去除多余空格

    # print(token_texts)
    print(type(token_texts))



    # 去除停用词
    # filtered_titles = [w for w in word_tokens if not w in stop_words]
    filtered_titles = [w for w in token_texts if not w in stop_words] # 去除停用词
    filtered_titles = [word for word in filtered_titles if word not in all_punctuation] # 去除标点符号

    print("filtered_titles len\n",len(filtered_titles)) # 字符串数量！

    # 将去除停用词后的词重新组合成字符串
    filtered_titles_text = ' '.join(filtered_titles)

    print(len(filtered_titles_text)) # 字符串长度！别被误导（所少个字符）
    # ====================================

    # 计算词权重
    word_weights,graph = textrank_weighted_word_graph(filtered_titles_text)

    # 保存pagerank算法后的词关系权重 可视化
    # 根据PageRank值更新边的权重
    # 记录权重关系 字典形式存储
    pagerank_weighted_graph = nx.Graph()
    for node, score in word_weights.items():
        pagerank_weighted_graph.add_node(node)

    for u, v, data in graph.edges(data=True):
        weight = data['weight'] * word_weights[u] * word_weights[v]
        pagerank_weighted_graph.add_edge(u, v, weight=weight)

    graph_content_file_name = f"./T4TitleTextRank/{model_CLS_name}/T4_{date_UNI}_{model_CLS_name}_graph_content.txt"
    with open('./T4TitleTextRank/graph_content.txt', 'w') as file:
        file.write(str(nx.to_dict_of_dicts(pagerank_weighted_graph)))

    sorted_words = sorted(word_weights.items(), key=lambda x: x[1], reverse=True)

    # 保存到新的CSV文件
    # word_weights_df = pd.DataFrame(word_weights.items(), columns=['word', 'weight'])
    word_weights_df = pd.DataFrame(sorted_words, columns=['word', 'weight'])

    word_weight_file_name = f"./T4TitleTextRank/{model_CLS_name}/T4_{date_UNI}_{model_CLS_name}_word_weight_new.csv"

    # word_weights_df.to_csv('./T4TitleTextRank/word_weight.csv', index=False)
    # word_weights_df.to_csv('./T4TitleTextRank/word_weight_new.csv', index=False)
    word_weights_df.to_csv(word_weight_file_name, index=False)

    # 接下来，计算每个标题的权重
    # 读取词权重文件
    # word_weights_df = pd.read_csv('./T4TitleTextRank/word_weight.csv')
    # word_weights_df = pd.read_csv('./T4TitleTextRank/word_weight_new.csv')
    word_weights_df = pd.read_csv(word_weight_file_name)


    # 将词权重转换为字典，方便查找
    word_weights = pd.Series(word_weights_df.weight.values, index=word_weights_df.word).to_dict()

    # print(word_weights)
    # 读取新闻标题文件
    titles_df = data_ORI
    # titles_df = pd.read_csv('./Data231202-231211/Data231202.csv')
    # titles_df = titles_df['title']



    # 定义一个函数，用于计算标题的权重
    def calculate_title_weight(title):
        doc = nlp(title)
        # 对标题进行分词并计算总权重
        return sum(word_weights.get(token.text, 0) for token in doc)  # 如果词不在word_weights中，则默认权重为0
        # return sum(word_weights.get(token.text, 0) for token in doc if token.text not in stop_words and token.text not in all_punctuation)  # 如果词不在word_weights中，则默认权重为0
        # return sum(word_weights.get(token.text, 0) for token in doc if token.text not in stop_words and token.text not in string.punctuation)  # 如果词不在word_weights中，则默认权重为0


    # 计算每个标题的权重
    titles_df['T4_title_weight'] = titles_df['title'].apply(calculate_title_weight)
    # print(titles_df['T4_title_weight'])

    # 根据权重排序并添加排名，相同权重的排名相同
    titles_df = titles_df.sort_values(by='T4_title_weight', ascending=False)
    titles_df['T4_rank'] = titles_df['T4_title_weight'].rank(method='min', ascending=False)

    # 对权重进行归一化处理，并存储结果到"S_scale"列
    scaler = MinMaxScaler()
    titles_df['T4_S_scale'] = scaler.fit_transform(titles_df[['T4_title_weight']])  # 归一化映射到分数！

    # # 创建"S_score"列
    # titles_df['T4_S_score'] = titles_df['T4_S_scale'] * 20

    # 创建"S_score"列
    titles_df['T4_S_score'] = titles_df['T4_S_scale'] * 100

    # 只保留需要的列
    T4_final_df = titles_df[['id','title', 'T4_title_weight', 'T4_rank', 'T4_S_scale', 'T4_S_score']]


    # 保存到新的csv文件
    # final_df.to_csv('./T4TitleTextRank/titles_weight.csv', index=False)

    T4_file_name = f"./T4TitleTextRank/{model_CLS_name}/T4_{date_UNI}_{model_CLS_name}_result_new.csv"
    # T4_final_df.to_csv('./T4TitleTextRank/titles_weight_new.csv', index=False)
    T4_final_df.to_csv(T4_file_name, index=False)




    # 提取新闻的category1进行类别评分

    # category_df = pd.read_csv('./T5CateforyScore/category_score.csv')
    category_df = pd.read_csv('./T5CateforyScore/category_score_FIX.csv')


    # Load the CSV file with news data
    # news_df = pd.read_csv('./Data231202-231211_FIX/Data231202_newDATA.csv')
    news_df = data_ORI


    # Merge the two DataFrames based on the "category1" column
    merged_df = pd.merge(news_df, category_df, how='left', left_on='category1', right_on='category')

    # Sort the merged DataFrame based on the "rank" column
    sorted_df = merged_df.sort_values(by='T5_rank')

    # Select the desired columns
    selected_columns = ['id','title', 'category1', 'T5_rank', 'T5_S_scale', 'T5_S_score']
    T5_final_df = sorted_df[selected_columns]

    T5_file_name = f"./T5CateforyScore/{model_CLS_name}/T5_{date_UNI}_{model_CLS_name}_result_new.csv"
    # Save the result to a new CSV file
    # T5_final_df.to_csv('./T5CateforyScore/Data231202_categoryScore_new.csv', index=False)
    T5_final_df.to_csv(T5_file_name, index=False)



    # T1_final_df :'id','T1_ori_indexFrom0', 'title', 'body', 'T1_clus_news_num', 'T1_rank','T1_S_scale', 'T1_S_score'
    # T2_final_df:'id','website_id', 'title', 'T2_S_score', 'T2_rank'
    # T3_final_df:'id','title', 'body_len', 'T3_rank','T3_S_scale', 'T3_S_score'
    # T4_final_df: 'id','title', 'T4_title_weight', 'T4_rank', 'T4_S_scale', 'T4_S_score'
    # T5_final_df:'id','title', 'category1', 'T5_rank', 'T5_S_scale', 'T5_S_score'
    # 合并5个dataframe：
    # 第一步:将T1_final_df和T2_final_df合并
    merged_df = pd.merge(T1_final_df, T2_final_df, on=['id', 'title'], how='outer')

    # 第二步:将第一步合并后的DataFrame与T3_final_df合并
    merged_df = pd.merge(merged_df, T3_final_df, on=['id', 'title'], how='outer')

    # 第三步:将第二步合并后的DataFrame与T4_final_df合并
    merged_df = pd.merge(merged_df, T4_final_df, on=['id', 'title'], how='outer')

    # 第四步:将第三步合并后的DataFrame与T5_final_df合并
    merged_df = pd.merge(merged_df, T5_final_df, on=['id', 'title'], how='outer')

    # 打印合并后的 DataFrame
    Merge_file_name = f"./MergeFiveDScore/{model_CLS_name}/Merge_{date_UNI}_{model_CLS_name}_FiveDScore_result_new.csv"
    # merged_df.to_csv('./MergeFiveDScore/FiveDScore_Merge.csv', index=False)
    merged_df.to_csv(Merge_file_name, index=False)

    # print(merged_df)


    # 假设权重 
    # w1, w2, w3, w4, w5 = 0.5,0.05,0.05,0.3,0.1
    # 权重设置思路：
    # ①层次分析法 根据各任务的重要性赋权
    # ②迭代 需要一个评估指标（正确个数？）来进行迭代找出模型最优权重！

    # 层次分析法权重！：
    # 通过进行层次分析法确定的五个维度权重为:相似新闻报道频率(0.46221)、新闻来源网站权威性(0.03503)、新闻标题重要性(0.35029)、新闻正文长度(0.03049)、新闻类别(0.12198)。
    # 对应
    # T1：0.46221 相似新闻---clusterScore
    # T2: 0.03503 网站权威性---WebsiteRank 
    # T3：0.03049 正文长度---bodyLenRank
    # T4：0.35029 新闻标题重要性 --- TitleTextRank
    # T5：0.12198 新闻类别 --- Category

    w1, w2, w3, w4, w5 = 0.46221, 0.03503, 0.03049, 0.35029, 0.12198


    # 计算总分数
    merged_df['total_S_score'] = w1 * merged_df['T1_S_score'] + w2 * merged_df['T2_S_score'] + w3 * merged_df['T3_S_score'] + w4 * merged_df['T4_S_score'] + w5 * merged_df['T5_S_score']

    # 生成排名
    merged_df['total_rank'] = merged_df['total_S_score'].rank(method='min', ascending=False)

    # 根据总分数降序排序
    merged_df = merged_df.sort_values('total_S_score', ascending=False)

    # 将结果保存到csv文件
    total_result_file_name = f"./MergeFiveDScore/{model_CLS_name}/total_result_{date_UNI}_{model_CLS_name}.csv"
    # merged_df.to_csv('./MergeFiveDScore/total_result.csv', index=False)
    merged_df.to_csv(total_result_file_name , index=False)


    selected_columns = ['id','T1_ori_indexFrom0', 'category1','title','body','total_S_score','total_rank']
    merged_df_pure =  merged_df[selected_columns]

    total_result_pure_file_name = f"./MergeFiveDScore/{model_CLS_name}/total_result_pure_{date_UNI}_{model_CLS_name}.csv"

    # Save the result to a new CSV file
    # merged_df_pure.to_csv('./MergeFiveDScore/total_result_pure.csv', index=False)
    merged_df_pure.to_csv(total_result_pure_file_name, index=False)
