import rich
import os
import json

from transformers import AutoModel, AutoTokenizer, BertModel, BertConfig
import torch
from torch import nn
from torch.optim import Adam
from database.mongo import get_training_data_collection
import numpy as np



# muli-label classification

class MIZUClassifier(BertModel):
    def __init__(self, n_class) -> None:
        super().__init__(BertConfig())
        
        self.bert = AutoModel.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')
        self.classifier = nn.Linear(312, n_class)
        self.loss_fn = nn.BCELoss()

    def forward(self, batch, is_training=True):
        out = self.bert(input_ids=batch['input_ids'], attention_mask=batch['attention_masks']).pooler_output # [bs, 312]
        logits = torch.sigmoid(self.classifier(out)) # [bs, n_class]
        
        # [0.1, 0.9, ..., 0.3] n_class
        
        if is_training:
            loss = self.loss_fn(logits, batch['labels'])
            return loss
        else:
            return logits


def get_batch(train_data, n_class, batch_size):
    tokenizer = AutoTokenizer.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')
    
    i = 0
    while i < len(train_data):
        batch = train_data[i: i+batch_size]
        
        input_ids = []
        attention_masks = []
        labels = []
        for d in batch:
            labels_tensor = torch.zeros([len(labels), n_class])
            for i in range(len(d['labels'])):
                labels_tensor[i][torch.tensor(labels[i])] = 1
            labels.append(labels_tensor)    
            
            input_ids.append(tokenizer.convert_tokens_to_ids([tokenizer.cls_token] + d['tokens'] + [tokenizer.sep_token]))
            attention_masks.append([1] * len(input_ids[-1]))
        
        # padding
        max_length = max([len(x) for x in input_ids])
        for i in range(len(input_ids)):
            input_ids[i] += [tokenizer.pad_token_id] * (max_length - len(input_ids[i]))
            attention_masks[i] += [0] * (max_length - len(input_ids[i]))

        yield {
            'input_ids': torch.tensor(input_ids, dtype=torch.long),
            'attention_masks': torch.tensor(attention_masks, dtype=torch.long),
            'labels': torch.tensor(labels, dtype=torch.long)
        }
    


def segmentation(corpus):
    # [(text, labels)]
    corpus = [(data["text"], data["domains"]) for data in corpus]
    rich.print("Start segmentation")
    
    if os.path.exists('label_dict.json'):
        label_to_id = json.load(open('label_dict.json'))
    else:
        label_set = set()
        for _, labels in corpus:
            label_set.update(labels)
        
        print(len(label_set))
        label_to_id = dict()
        for l in label_set:
            if l not in label_to_id:
                label_to_id[l] = len(label_to_id)
        json.dump(label_to_id, open('label_dict.json', 'w'), indent=2)
        
    train_data = []
    tokenizer = AutoTokenizer.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')
    for text, labels in corpus:
        tokens = tokenizer.tokenize(text)
        if len(tokens) > 510:
            continue
            _i = 0
            
        # train_data.append((tokens, [label_to_id[l] for l in labels]))
        train_data.append({
            'tokens': tokens,
            'labels': [label_to_id[l] for l in labels]
        })
    return train_data



def evaluate(test_data):
    # precision, recall, f1
    # f1 = 2*p*r / (p+r)
    p_list = []
    r_list = []
    f1_list = []
    for batch in get_batch(test_data, n_class, 500):
        probs = model(batch, is_training=False)
        pred_labels = probs > 0.5 # [1, 3, 8, 9, 10]
        labels = batch['labels'] # [0, 3, 5, 8]
        for pred, gt in zip(pred_labels, labels):
            pred = torch.nonzero(pred).data.cpu().numpy().tolist()
            gt = torch.nonzero(gt).data.cpu().numpy().tolist()
            
            p = 0
            if len(pred):
                for x in pred:
                    if x in gt:
                        p += 1
                p /= len(pred)
            r = 0
            if len(gt):
                for x in gt:
                    if x in pred:
                        r += 1
                r /= len(gt)
            f1 = 0
            if p + r > 0:
                f1 = 2*p*r / (p + r)
            
            p_list.append(p)
            r_list.append(r)
            f1_list.append(f1)

    avg_f1 = np.mean(f1_list)
    return avg_f1


if __name__ == "__main__":
    n_class = 10
    model = MIZUClassifier(n_class=n_class)
    
    optimizer = Adam(model.parameters(), lr=3e-5)
    data = get_training_data_collection().find()
    rich.print("Data fetched")
    train_data = segmentation(data)
    rich.print("Training data fetched")
    
    best_f1 = 0
    step = 0
    for epoch in range(1):
        for batch in get_batch(train_data, n_class, 500):
            loss = model(batch)
            
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            step += 1
            if step % 50 == 0:
                print(f'Step {step}: {loss.item()}')
            
            if step % 200 == 0:
                
                cur_f1 = evaluate(train_data)
                print(cur_f1, best_f1)
                if cur_f1 > best_f1:
                    model.save_pretrained('./mizu_classifier')
                    best_f1 = cur_f1

    # model.push_to_hub()
    # model = MIZUClassifier(n_class=n_class).from_pretrained('saved_model')
    # model.push_to_hub()
