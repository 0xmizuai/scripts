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


def evaluate(model, test_data, n_class, device, t=0.01):
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
        pred_labels = probs > t # [1, 3, 8, 9, 10]
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
    
    with open(segmentation_file, "r") as f:
        seg_data = json.load(f)
        all_data = seg_data["all_data"]
        n_class = seg_data["n_class"]

    dev_data = all_data[0:2000]
    
    model = AutoModelForSequenceClassification.from_pretrained('./mizu_classifier', num_labels=n_class)
    model.to(device)
    
    thresholds = [1e-2, 5e-2, 1e-1, 2e-1, 3e-1, 5e-1]
    
    for t in range(1, 21):
        t1 = 0.03 + t / 1000.
        f1 = evaluate(model, dev_data, n_class, device, t1)
        print(f'T: {t1}, f1: {f1}')
