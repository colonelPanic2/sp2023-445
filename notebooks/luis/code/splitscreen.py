import torch
t = torch.tensor([[1, 2, 3, 4, 5, 6],
                  [7, 8, 9, 10, 11, 12],
                  [13, 14, 15, 16, 17, 18],
                  [19, 20, 21, 22, 23, 24]])
t = torch.rand(8,12)
H,W = t.shape
H,W = H//2,W//3
T = ['TL','TM','TR','BL','BM','BR']
def map_to_block_index(r,c,dims=(720,1278),err=False):
    col_blocks = dims[1]//3
    row_blocks = dims[0]//2
    T_index = (c//col_blocks) + 3*(r>=row_blocks)
    return T_index
print(f"t.shape: {t.shape}")
print(f"T.shape: {torch.tensor([len(T)])}")
for r in range(t.shape[0]):
    print("[",end=' ')
    for c in range(t.shape[1]):
        T_index = map_to_block_index(r,c,t.shape)
        
        try:
            print(T[T_index],end=' ')
        except:
            map_to_block_index(r,c,t.shape,True)
            break
        # print(f"t({r},{c}) = {t[r][c]} -> T({T_index}) = {T[T_index]}")
    print("]")
# Split t into 6 tensors
t_list = torch.split(t, split_size_or_sections=[W,W,W], dim=1)
t_list = [torch.split(x, split_size_or_sections=[H,H], dim=0) for x in t_list]
(TL,BL), (TM,BM), (TR,BR) = t_list
T = torch.tensor([TL.tolist(),TM.tolist(),TR.tolist(),BL.tolist(),BM.tolist(),BR.tolist()])
