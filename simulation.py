import numpy as np
import random
import pandas as pd


class Person(object):
    def __init__(self, arrive_time, is_special=False) -> None:
        self.arrive_time = arrive_time
        self.is_special = is_special
        self.ride_time_to_seolip = (1.5848929430742282, 0.7955861513566723, 541.7394666657118,
                                    377.26053333428825)  # beta분포, alpha, beta, location, scale, 설입까지 버스 타는 시간
        self.bus_count = 0
        self.wait_time = 0
        self.total_time = 0

    def ride_5511(self, time):
        if self.is_special:
            self.bus_count += 1
            self.wait_time += time - self.arrive_time
            self.total_time = self.wait_time + round(
                np.random.default_rng().beta(self.ride_time_to_seolip[0], self.ride_time_to_seolip[1]) *
                self.ride_time_to_seolip[3] + self.ride_time_to_seolip[2])

    def couldnt_ride_5511(self):
        if self.is_special:
            self.bus_count += 1


class BusSimulation(object):
    def __init__(self, time_special) -> None:
        self.time_special = time_special
        self.special_person = Person(time_special, True)

        # 처음 돌릴때 필요한 변수
        self.first_5511 = (18146.714285714286, 34.97229223956869)  # 정규분포 mu, sigma값, 첫 5511 시각
        self.first_5516 = (18120.0, 259.375)  # 지수분포 location(원점값), scale(lambda 역수), 첫 5516 도착 시각
        self.first_chago = (213485839.75521147, 18566.862108442438, 268.92220358051526)  # t분포 자유도값, 평균값(location, 더해줘야 함), scale, 첫 차고지차 도착 시각
        self.initial_waiting = (3.0, 10.666666666666666)  # 지수분포, 5:00에 대기하는 사람 수

        # 돌리면서 필요한 변수 - 처음 돌릴때도 넣어야 하는 변수
        self.adding_rate = (1, 44.40634005763689)  # 지수분포, 사람 오는 주기
        self.adding_randvar = {0: 0, 1: 0.777142857, 2: 0.954285714, 3: 0.985714285, 4: 0.991428571, 5: 0.997142857,
                               6: 1}  # 한번에 오는 비율(누적분포)
        self.departing_rate = (
        3.292105716403076, -13.287827135466838, 119.17062480056617)  # chi2분포 자유도값, location, scale, 이탈 주기
        self.departing_randvar = {0: 0, 1: 0.96875, 2: 1}  # 이탈 비율 (누적분포)

        # 돌리면서 필요한 변수 - 돌리면서 넣어야 하는 변수
        self.arrive_period_5516 = (20.005584766647246, -406.20303832870525, 54.699676358259936)  # chi2분포, 5516 도착주기
        self.ride_rate_5516 = 194 / 663  # 5516 타는 비율
        self.arrive_period_chago = (
        16.98237077685359, -673.7165670743836, 81.58805945154745)  # 감마분포 a값, location값, scale값, 차고지버스 도착주기
        self.ride_rate_chago = 71 / 294  # 차고지 타는 비율
        self.arrive_period_5511 = (17.530120930815443, 610.2002236846756, 146.12021373027414)  # t분포, 5511 도착주기
        self.no_leftover = 0.42  # 다 타는 비율
        self.leftover_rate = (0.040000000000000036, 0.2818909585146091)  # 지수분포, 못 타는 비율
        self.ride_rate_2029 = (7347376.22191485, 0.9007288565261925, 0.0693921890903089)  # t분포, 20-29분 타는 비율
        self.ride_rate_3039 = (0.9165266106442578, 0.1360202861868794)  # 정규분포, 30-39분 타는 비율

        self.bus_lane = [Person(18000) for _ in
                         range(round(self.initial_waiting[0] + np.random.exponential(self.initial_waiting[1])))]

    def calculate_distance(self, kind) -> float:
        ''' 
        kind: "arrive", "depart", "5511", "5516", "chago"
        '''
        return_var = 0
        if kind == "arrive":
            return_var = round(
                np.random.default_rng().exponential(self.adding_rate[1]) + self.adding_rate[0]
            )

        elif kind == "depart":
            return_var = round(
                self.departing_rate[2] * np.random.default_rng().chisquare(self.departing_rate[0]) +
                self.departing_rate[1]
            )

        elif kind == "5511":
            return_var = round(
                self.arrive_period_5511[2] * np.random.default_rng().standard_t(self.arrive_period_5511[0]) +
                self.arrive_period_5511[1]
            )

        elif kind == "5516":
            return_var = round(
                self.arrive_period_5516[2] * np.random.default_rng().chisquare(self.arrive_period_5516[0]) +
                self.arrive_period_5516[1]
            )

        elif kind == "chago":
            return_var = round(
                np.random.default_rng().gamma(self.arrive_period_chago[0], self.arrive_period_chago[2]) +
                self.arrive_period_chago[1]
            )

        else:
            raise ValueError("맞는 단어 쳐 느라")

        if return_var < 0:
            return 0.0
        else:
            return return_var

    def choose_other_buses(self, depart_ratio):
        unimportant_index = [i for i in range(len(self.bus_lane)) if not self.bus_lane[i].is_special]
        important_index = [i for i in range(len(self.bus_lane)) if self.bus_lane[i].is_special]
        sample_number = round(depart_ratio * len(self.bus_lane))
        try:
            out_index = random.sample(unimportant_index, sample_number)
        except ValueError:
            out_index = unimportant_index

        for i in out_index:
            self.bus_lane[i] = 0

        self.bus_lane = list(filter(lambda x: x != 0, self.bus_lane))

    def run(self):
        f = open("debug.txt", 'w')
        # start
        arrive_5511_time = round(np.random.normal(self.first_5511[0], self.first_5511[1]))
        arrive_5516_time = round(self.first_5516[0] + np.random.exponential(self.first_5516[1]))
        arrive_chago_time = round(self.first_chago[1] + np.random.standard_t(self.first_chago[0]))
        arrive_people_time = 18000 + self.calculate_distance("arrive")
        depart_people_time = 18000 + self.calculate_distance("depart")

        # update
        time = 17999
        flag = False  # 특별한 애가 5511을 탔는지 검사
        while not flag:
            time += 1
            f.write(str(time) + '\n')
            f.write(str([arrive_5511_time, arrive_5516_time, arrive_chago_time, arrive_people_time, depart_people_time]) + '\n')
            f.write(str([(p.arrive_time, p.is_special) for p in self.bus_lane]) + '\n')
            # 측정자 도착(0순위)
            if time == self.time_special:
                self.bus_lane.append(self.special_person)
                f.write("arrived\n")

            # 사람 도착(1순위)
            while time == arrive_people_time:
                rand_num = random.random()
                for key in self.adding_randvar.keys():
                    if rand_num == 1:
                        self.bus_lane.extend([Person(time)] * 6)
                        break
                    elif self.adding_randvar[key] <= rand_num < self.adding_randvar[key + 1]:
                        self.bus_lane.extend([Person(time)] * (key + 1))
                        break
                arrive_people_time += self.calculate_distance("arrive")
                f.write("arrive -> \n" + str([(p.arrive_time, p.is_special) for p in self.bus_lane]) + '\n')

            # 이탈(2순위)
            while time == depart_people_time:
                rand_num = random.random()
                for key in self.departing_randvar.keys():
                    try:
                        if rand_num == 1:
                            for _ in range(2):
                                if not self.self.bus_lane[0].is_special:
                                    self.bus_lane.pop(0)
                                else:
                                    self.bus_lane.pop(1)
                            break
                        elif self.departing_randvar[key] <= rand_num < self.departing_randvar[key + 1]:
                            for _ in range(key + 1):
                                if not self.bus_lane[0].is_special:
                                    self.bus_lane.pop(0)
                                else:
                                    self.bus_lane.pop(1)
                            break
                    except IndexError:
                        pass

                depart_people_time += self.calculate_distance("depart")
                f.write("depart -> \n" + str([(p.arrive_time, p.is_special) for p in self.bus_lane]) + '\n')

            # 5511(3순위)
            while time == arrive_5511_time and flag == False:
                # 몇명 타는지 정하기
                if 19200 <= time < 19800:
                    depart_ratio = np.random.default_rng().standard_t(self.ride_rate_2029[0]) * self.ride_rate_2029[2] + \
                                   self.ride_rate_2029[1]
                elif 19800 <= time < 20400:
                    depart_ratio = np.random.default_rng().normal(self.ride_rate_3039[0], self.ride_rate_3039[1])
                else:
                    all_ride_decide = random.random()
                    if all_ride_decide > 0.58:
                        depart_ratio = 1
                    else:
                        depart_ratio = 1 - (
                                    np.random.default_rng().exponential(self.leftover_rate[1]) + self.leftover_rate[0])
                if depart_ratio < 0:
                    depart_ratio = 0
                elif depart_ratio > 1:
                    depart_ratio = 1
                depart_people = round(len(self.bus_lane) * depart_ratio)

                # 태우기
                for _ in range(depart_people):
                    try:
                        if self.bus_lane[0].is_special:
                            self.bus_lane[0].ride_5511(time)
                            flag = True
                            break
                        self.bus_lane.pop(0)
                    except:
                        pass

                # 못탄놈 체크
                if not flag:
                    for people in self.bus_lane:
                        people.couldnt_ride_5511()

                arrive_5511_time += self.calculate_distance("5511")
                f.write(f"5511 -> {depart_people} \n" + str([(p.arrive_time, p.is_special) for p in self.bus_lane]) + '\n')

            # 5516(4순위)
            while time == arrive_5516_time:
                self.choose_other_buses(self.ride_rate_5516)
                arrive_5516_time += self.calculate_distance("5516")
                f.write(f"5516 -> \n" + str([(p.arrive_time, p.is_special) for p in self.bus_lane]) + '\n')

            # 차고지(4순위)
            while time == arrive_chago_time:
                self.choose_other_buses(self.ride_rate_chago)
                arrive_chago_time += self.calculate_distance("chago")
                f.write(f"chago -> \n" + str([(p.arrive_time, p.is_special) for p in self.bus_lane]) + '\n')

            f.write('\n')

        return self.special_person


iteration = 100
whole_df = pd.DataFrame(np.zeros((90, 1)), index=[f"{5 + int(i / 60)}{i - 60 * (i // 60):2d}" for i in range(90)])

for i in range(iteration):
    tmp_df = pd.DataFrame(np.zeros((90, 3)), index=[f"{5 + int(i / 60)}{i - 60 * (i // 60):2d}" for i in range(90)])
    tmp_df.columns = [
        f"{i}_총 본 버스 수",
        f"{i}_정류장에서 기다린 시간",
        f"{i}_총 걸린 시간"
    ]
    for time in range(18000, 23400, 60):
        sim = BusSimulation(time)
        p = sim.run()
        tmp_df.iloc[int((time - 18000) / 60), :] = [p.bus_count, p.wait_time, p.total_time]
    whole_df = pd.merge(whole_df, tmp_df, left_index=True, right_index=True)
whole_df = whole_df.drop([0], axis=1)
whole_df.to_excel("중간정리.xlsx")
print("fin")