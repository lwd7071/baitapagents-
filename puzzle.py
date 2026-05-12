import random
import copy
import time

MUC_TIEU = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 0]
]

def in_bang(bang):
    for dong in bang:
        print(f"{dong}")
    print("------")

def tim_vi_tri_trong(bang):
    for dong in range(3):
        for cot in range(3):
            if bang[dong][cot] == 0:
                return dong, cot
    return -1, -1

def dem_o_sai(bang):
    sai = 0
    for i in range(3):
        for j in range(3):
            if bang[i][j] != 0 and bang[i][j] != MUC_TIEU[i][j]:
                sai += 1
    return sai

def thuc_thi_di_chuyen(bang, hanh_dong, dong_trong, cot_trong):
    bang_moi = copy.deepcopy(bang)
    if hanh_dong == "len":
        bang_moi[dong_trong][cot_trong], bang_moi[dong_trong-1][cot_trong] = bang_moi[dong_trong-1][cot_trong], bang_moi[dong_trong][cot_trong]
    elif hanh_dong == "xuong":
        bang_moi[dong_trong][cot_trong], bang_moi[dong_trong+1][cot_trong] = bang_moi[dong_trong+1][cot_trong], bang_moi[dong_trong][cot_trong]
    elif hanh_dong == "trai":
        bang_moi[dong_trong][cot_trong], bang_moi[dong_trong][cot_trong-1] = bang_moi[dong_trong][cot_trong-1], bang_moi[dong_trong][cot_trong]
    elif hanh_dong == "phai":
        bang_moi[dong_trong][cot_trong], bang_moi[dong_trong][cot_trong+1] = bang_moi[dong_trong][cot_trong+1], bang_moi[dong_trong][cot_trong]
    return bang_moi

# tao bang random bang cach xao tron tu bang muc tieu de chac chan giai duoc
def tao_bang_ngau_nhien(so_buoc_xao=20):
    bang = copy.deepcopy(MUC_TIEU)
    for _ in range(so_buoc_xao):
        dong, cot = tim_vi_tri_trong(bang)
        huong_di = []
        if dong > 0: huong_di.append("len")
        if dong < 2: huong_di.append("xuong")
        if cot > 0: huong_di.append("trai")
        if cot < 2: huong_di.append("phai")
        
        huong = random.choice(huong_di)
        bang = thuc_thi_di_chuyen(bang, huong, dong, cot)
    return bang

#bang truoc do
def tap_luat(bang_hien_tai, bang_truoc_do):
    dong, cot = tim_vi_tri_trong(bang_hien_tai)
    
    huong_co_the_di = []
    if dong > 0: huong_co_the_di.append("len")
    if dong < 2: huong_co_the_di.append("xuong")
    if cot > 0: huong_co_the_di.append("trai")
    if cot < 2: huong_co_the_di.append("phai")
    
    sai_hien_tai = dem_o_sai(bang_hien_tai)
    huong_khong_bi_ngu = [] # cac huong khong lam quay lai buoc truoc

    # loc ra cac huong di khong bi trung lai trang thai cu
    for huong in huong_co_the_di:
        bang_thu = thuc_thi_di_chuyen(bang_hien_tai, huong, dong, cot)
        
        # neu chua co bang truoc do, hoac buoc nay ko lam quay lui
        if bang_truoc_do is None or bang_thu != bang_truoc_do:
            huong_khong_bi_ngu.append(huong)
            
            # neu buoc nay ngon (giam o sai) thi quat luon
            if dem_o_sai(bang_thu) < sai_hien_tai:
                return huong, dong, cot
                
    # neu ko co buoc nao giam o sai, chon random 1 buoc trong cac buoc khong lui
    if len(huong_khong_bi_ngu) > 0:
        return random.choice(huong_khong_bi_ngu), dong, cot
        
    # truong hop bat dac di ket qua thi buoc phai quay lui
    return random.choice(huong_co_the_di), dong, cot

if __name__ == "__main__":
    # tao ma tran dau vao ngau nhien
    bang_hien_tai = tao_bang_ngau_nhien(so_buoc_xao=15)
    bang_truoc_do = None
    
    print("Bang ban dau (random):")
    in_bang(bang_hien_tai)

    so_buoc_toi_da = 100
    
    for buoc in range(so_buoc_toi_da):
        if bang_hien_tai == MUC_TIEU:
            print("Giai quyet xong!")
            break
            
        # dua ca hien tai va qua khu vao de xet luat
        huong, dong_trong, cot_trong = tap_luat(bang_hien_tai, bang_truoc_do)
        print(f"Buoc {buoc + 1}: Di chuyen sang '{huong}'")
        
        # luu lai trang thai de dung cho buoc sau
        bang_truoc_do = copy.deepcopy(bang_hien_tai)
        
        # thuc hien di chuyen
        bang_hien_tai = thuc_thi_di_chuyen(bang_hien_tai, huong, dong_trong, cot_trong)
        
        in_bang(bang_hien_tai)
        time.sleep(0.5)