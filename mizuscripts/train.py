import random
import rich
from rich.progress import Progress
import os
from os.path import exists
import json
import time

from transformers import AutoModel, AutoTokenizer, BertModel, BertConfig, AutoModelForSequenceClassification
import torch
from torch import nn
from torch.optim import Adam
import numpy as np
from database.mongo import get_training_data_collection

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


def get_batch(train_data, n_class, batch_size, device):
    random.shuffle(train_data)
    tokenizer = AutoTokenizer.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')
    
    i = 0
    while i < len(train_data):
        batch = train_data[i: i+batch_size]
        
        input_ids = []
        attention_masks = []
        labels = []
        for d in batch:
            labels_tensor = torch.zeros([n_class])
            for _li in range(len(d['labels'])):
                labels_tensor[d['labels'][_li]] = 1
            labels.append(labels_tensor)    
            
            input_ids.append(tokenizer.convert_tokens_to_ids([tokenizer.cls_token] + d['tokens'] + [tokenizer.sep_token]))
            attention_masks.append([1] * len(input_ids[-1]))
        
        # padding
        max_length = max([len(x) for x in input_ids])
        for j in range(len(input_ids)):
            input_ids[j] += [tokenizer.pad_token_id] * (max_length - len(input_ids[j]))
            attention_masks[j] += [0] * (max_length - len(attention_masks[j]))

        i += batch_size
        yield {
            'input_ids': torch.tensor(input_ids, dtype=torch.long).to(device),
            'attention_masks': torch.tensor(attention_masks, dtype=torch.long).to(device),
            'labels': torch.stack(labels).float().to(device),
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
        
        rich.print(len(label_set))
        label_to_id = dict()
        for l in label_set:
            if l not in label_to_id:
                label_to_id[l] = len(label_to_id)
        json.dump(label_to_id, open('label_dict.json', 'w'), indent=2)
        
    train_data = []
    tokenizer = AutoTokenizer.from_pretrained('huawei-noah/TinyBERT_General_4L_312D')
    with Progress() as progress:
        task = progress.add_task("Segementation: ", total=len(corpus))
        for text, labels in corpus:
            progress.advance(task_id=task, advance=1)
            tokens = tokenizer.tokenize(text)
            if len(tokens) > 510:
                continue
                _i = 0
                
            # train_data.append((tokens, [label_to_id[l] for l in labels]))
            train_data.append({
                'tokens': tokens,
                'labels': [label_to_id[l] for l in labels]
            })
    return train_data, len(label_to_id)


def evaluate(model, test_data, n_class, device):
    # precision, recall, f1
    # f1 = 2*p*r / (p+r)

    p_list = []
    r_list = []
    f1_list = []
    model.eval()
    for batch in get_batch(test_data, n_class, 400, device):
        with torch.no_grad():
            logits = model(input_ids=batch['input_ids'], attention_mask=batch['attention_masks']).logits
            probs = torch.sigmoid(logits)
            # print(logits.shape, probs.shape)
        pred_labels = probs > 0.01 # [1, 3, 8, 9, 10]
        labels = batch['labels'] # [0, 3, 5, 8]

        for pred, gt in zip(pred_labels, labels):
            pred = set(torch.nonzero(pred).squeeze(-1).data.cpu().numpy().tolist())
            gt = set(torch.nonzero(gt).squeeze(-1).data.cpu().numpy().tolist())

            n_inter = len(pred.intersection(gt))
            if n_inter == 0:
                p_list.append(0)
                r_list.append(0)
                f1_list.append(0)
            elif len(pred) == 0:
                p_list.append(0)
                r_list.append(0)
                f1_list.append(0)
            else:
                _p = n_inter / len(pred)
                _r = n_inter / len(gt)
                p_list.append(_p)
                r_list.append(_r)
                f1_list.append(2*_p*_r / (_p + _r))

            # print(pred)
            # print(gt)


    p = np.mean(p_list)
    r = np.mean(r_list)
    f1 = np.mean(f1_list)
    print(p, r, f1)
    return f1



if __name__ == "__main__":
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    segmentation_file = "segamentation.json"
    
    rich.print("Data fetched")
    if exists(segmentation_file):
        with open(segmentation_file, "r") as f:
            seg_data = json.load(f)
            all_data = seg_data["all_data"]
            n_class = seg_data["n_class"]
    else:
        collection = get_training_data_collection()
        total_count = collection.count_documents({})
        speed = 10000
        data_list = []
        with Progress() as progress:
            task = progress.add_task("Loading training data:", total=total_count)
            while len(data_list) != total_count:
                fetched = list(collection.find().limit(speed).skip(len(data_list)))
                progress.advance(task_id=task, advance=len(fetched))
                data_list.extend(fetched)
        domain_threshold = 1738
        domains = set()
        for data in data_list:
            data_domains = data["domains"]
            domains.update(data_domains)
            if len(domains) >= domain_threshold:
                break
        data_list = list(filter(lambda data: len(set(data["domains"]) & domains) != 0, data_list))
        for data in data_list:
            data["domains"] = set(data["domains"]) & domains
        print(len(domains))
        print(len(data_list))
        all_data, n_class = segmentation(data_list)
        with open(segmentation_file, "w") as f:
            f.write(json.dumps({
                "all_data": all_data,
                "n_class": n_class,
            }))
    rich.print(f"n_class: {n_class}")
    training_data = all_data[2000:]
    #training_labels = set()
    #for data in training_data:
    #    training_labels.update(data["labels"])
    # dev_data = list(filter(lambda data: len(set(data["labels"]) & training_labels) > 0, all_data[0:2000]))
    dev_data = all_data[0:2000]
    # rich.print(f"Number of labels: {len(training_labels)}")
    # rich.print(f"Number of dev data: {len(dev_data)}")
    model = AutoModelForSequenceClassification.from_pretrained('huawei-noah/TinyBERT_General_4L_312D', num_labels=n_class)     
    model.to(device)
    model.train()
    
    optimizer = Adam(model.parameters(), lr=0.00001)
    rich.print("Training data fetched")
    
    best_f1 = 0
    step = 0
    
    rich.print('Training....')
    start_t = time.time()
    
    for epoch in range(10):
        for batch in get_batch(training_data, n_class, 128, device):
            loss = model(input_ids=batch['input_ids'], attention_mask=batch['attention_masks'], labels=batch['labels']).loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            
            if step % 5 == 0:
                time_used = (time.time() - start_t) / 60
                rich.print(f'Step {step}: {round(loss.item(), 3)}, time used: {round(time_used, 1)} minutes')
            
            if step % 100 == 0:
                rich.print('Evaluating...')
                cur_f1 = evaluate(model, dev_data, n_class, device)
                rich.print(cur_f1)
                rich.print(f'Current F1: {cur_f1}, best F1 so far: {best_f1}')
                if cur_f1 > best_f1:
                    model.save_pretrained('./mizu_classifier')
                    best_f1 = cur_f1
                    print('model saved.')
                model.train()
            
            step += 1

    # model = MIZUClassifier(n_class=n_class).from_pretrained('./mizu_classifier')
    model.push_to_hub("mizu_classifier")
