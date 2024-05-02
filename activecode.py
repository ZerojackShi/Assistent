from mur.admin import *
my_crypt = Crypt()
a_machine_code = input('请输入机器码：')  
days = input('请输入授权天数：')    # 0 表示永久
a_user_code = gen_user_code(days, my_crypt)
a_register_code = gen_register_code(
    a_machine_code, a_user_code, my_crypt
)
print(a_register_code, a_user_code, a_machine_code)