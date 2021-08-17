import pandas as pd
import pathlib
import os


class Data_merge_manager():
    def __init__(self):
        self.dataframe = pd.DataFrame()
        self.path = f"{pathlib.Path().absolute()}/data/raw"
        self.name = "test_name"
    
    def set_name(self, name):
        self.name = name
    
    def create_final_df(self):
        id = 1
        for root, dirs, files in os.walk(self.path):
            for i in files:
                data = pd.read_csv(f"data/raw/{i}")
                data.insert(0, 'acquisition', id)
                self.dataframe = pd.concat([self.dataframe, data], ignore_index=True)
                
                self.dataframe = self.dataframe.drop(["Unnamed: 0"], axis=1)
                self.dataframe.to_csv(f"data/{self.name}.csv")
                id+=1

if __name__=="__main__":
    test = Data_merge_manager()
    test.set_name("short_data_motion_test")
    test.create_final_df()
