import datetime
import hassapi as hass
import time

	# Declare Class
	#entity="input_datetime.appdeamon_date"
class gardenIrrigation(hass.Hass):

	current_handle = None

	current_zone_index = -1
	init_try_count = 0

	def construct_entities(self):

		days_entity = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
		day_entity = "input_boolean.cycle{0}_{1}"
		duration_entity = "input_number.cycle{0}_zone{1}_duration"
		enable_entity = "input_boolean.cycle{0}_enable"
		time_entity = "input_datetime.cycle{0}_schedule_time"
		manualRun_entity = "input_boolean.cycle{0}_manual_run"
		manualRun_delayed_entity = "input_boolean.cycle{0}_manual_run_delayed"
		cycle_running_entity = "input_boolean.cycle{0}_running"
		zone_entity = "switch.zone_{0}"
		state_entity = "input_text.current_status"
		cycle_status_entity = "input_text.cycle{0}_current_status"
		cycle_multiplier_entity = "input_number.cycle{0}_multiplier"

		self.zone_durations_id= []
		self.active_days_id = []
		self.zones_id = []

		day_entity = day_entity.replace("{0}", self.cycle)
		for i in range(7):
			self.active_days_id.append(day_entity.replace("{1}", days_entity[i]))

		duration_entity = duration_entity.replace("{0}", self.cycle)
		for i in range(self.zone_count):
			self.zone_durations_id.append(duration_entity.replace("{1}", str(i+1)))
			self.zones_id.append(zone_entity.replace("{0}", str(i+1)))
			self.turn_off(self.zones_id[i])

		self.enable_id = enable_entity.replace("{0}", self.cycle)
		self.run_time_id = time_entity.replace("{0}", self.cycle)
		self.manual_run_delayed_id = manualRun_delayed_entity.replace("{0}", self.cycle)
		self.cycle_running_id = cycle_running_entity.replace("{0}", self.cycle)
		self.state_id = state_entity.replace("{0}", self.cycle)
		self.cycle_status_id = cycle_status_entity.replace("{0}", self.cycle)
		self.cycle_multiplier_id = cycle_multiplier_entity.replace("{0}", self.cycle)



	def initialize(self):
		try:
			self.cycle = str(self.args["cycle_id"])
			self.zone_count = int(self.args["zone_count"])
			self.construct_entities()

			self.turn_off(self.manual_run_delayed_id)
			self.turn_off(self.cycle_running_id)

			#days
			for day in self.active_days_id:
				self.listen_state(self.schedule_change, day)
			self.listen_state(self.schedule_change, self.run_time_id)
			self.listen_state(self.manual_run_delayed, self.cycle_running_id)
			self.listen_state(self.manual_run, self.manual_run_delayed_id)
			self.listen_state(self.cycle_runnig_change, self.cycle_running_id)
			self.listen_state(self.schedule_change, self.enable_id)
			self.schedule_change("None", "", "", "", "")
			self.log("Cylce "+self.cycle+" initialization complete.")
		except:
			if(self.init_try_count < 5):
				import sys
				self.log("There was an error in initialization, will try again in 1 minute.\nUnexpected error:"+ str(sys.exc_info()[0]))
				target_time = datetime.datetime.now()
				target_time = target_time + datetime.timedelta(minutes=1)
				self.init_try_count += 1
				self.run_at(self.reinitialize, target_time)
			else:
				self.log("There was 5 errors in initialization, notifying admin.")
				#IMPLEMENT

	def reinitialize(self, kwargs):
		initialize()

	def manual_run_delayed(self, entity, attribute, old, new, kwargs):
		target_time = datetime.datetime.now()
		target_time = target_time + datetime.timedelta(seconds=5)
		self.manual_run_handle = self.run_at(self.manual_run_delay_time, target_time)

	def manual_run_delay_time(self, kwargs):
		self.cancel_timer(self.manual_run_handle)
		if(self.get_state(self.cycle_running_id) == "on" and self.current_zone_index == -1):
			self.turn_on(self.manual_run_delayed_id)
		elif(self.current_zone_index != -1):
			self.turn_off(self.manual_run_delayed_id)

	
	def manual_run(self, entity, attribute, old, new, kwargs):
		if(entity == self.manual_run_delayed_id):
			if(new == "on"):
				self.log("Starting cycle " + str(self.cycle))
				self.start_cycle("")
			elif(new == "off"):
				self.log("Stopping cycle " + str(self.cycle))
				self.stop_cycle("")

	def schedule_change(self, entity, attribute, old, new, kwargs):
		if(self.enable_id == entity):
			if(new == "on"):
				self.log("Schedule enabled")
			elif(new == "off"):
				self.log("Schedule disabled")

		if(self.get_state(self.enable_id) == "on"):
			self.calculate_next_time()
		else:
			self.set_cycle_status("Disabled")

	def cycle_runnig_change(self, entity, attribute, old, new, kwargs):
		if(new == "off" and self.current_zone_index != -1):
			self.log("Manually stopping cycle")
			self.stop_cycle("")

	def calculate_next_time(self):
		if(self.current_handle):
			self.cancel_timer(self.current_handle)
		now = datetime.datetime.now()
		irrigation_time = None
		for i in range(7):
			if("on" == self.get_state(self.active_days_id[now.weekday()])):
				run_time = self.get_state(self.run_time_id)
				run_time = datetime.datetime.strptime(run_time, "%H:%M:%S")
				run_time = run_time.time()
				now_time = now.time()
				#will run in that day
				if(i == 0):
					#check for time for today
					if(run_time > now_time):
						#today
						irrigation_time = now.replace(hour = run_time.hour, minute = run_time.minute, second = run_time.second)	
						break
					else:
						#check for next day
						now = now.replace(day = now.day + 1)
				else:
					irrigation_time = now.replace(hour = run_time.hour, minute = run_time.minute, second = run_time.second)
					break
			else:
				#check for next day
				now = now + datetime.timedelta(days = 1)
		else:
			now_now = datetime.datetime.now()
			#never
			if("on" == self.get_state(self.active_days_id[now_now.weekday()])):
				#next week today
				irrigation_time = now_now.replace(hour = run_time.hour, minute = run_time.minute, second = run_time.second)
				irrigation_time = irrigation_time + datetime.timedelta(days = 7)
		###IMPLEMENT set scheduled time with call service
		if(irrigation_time != None):
			now = datetime.datetime.now()
			if(now.weekday() != irrigation_time.weekday()):
				if(irrigation_time.strftime("%A") == "Wednesday"):
					self.set_cycle_status(irrigation_time.strftime("Wed %H:%M"))
				else:
					self.set_cycle_status(irrigation_time.strftime("%A %H:%M"))

			else:
				self.set_cycle_status(irrigation_time.strftime("Today %H:%M"))
			self.current_handle = self.run_at(self.start_cycle, irrigation_time)
		else:
			self.set_cycle_status("No active day")


	def start_cycle(self, kwargs):
		self.set_cycle_status("Starting")
		self.log("Starting cylce" + self.cycle)
		self.turn_on(self.cycle_running_id)
		self.current_zone_index = 0
		target_time = datetime.datetime.now()
		target_time = target_time + datetime.timedelta(seconds=1)
		self.current_handle = self.run_at(self.next_zone, target_time)

	def next_zone(self, kwargs):
		self.current_zone_index += 1
		if(self.current_zone_index != 0):
			self.disable_zone(self.current_zone_index-1)
		target_time = datetime.datetime.now()
		duration = float(self.get_state(self.zone_durations_id[self.current_zone_index]))
		duration = duration * 0.01 * float(self.get_state(self.cycle_multiplier_id))
		minute = duration//1
		second = (duration%1)*60
		target_time = target_time + datetime.timedelta(seconds=second+1,minutes=minute)

		self.set_cycle_status("Zone "+ str(self.current_zone_index+1) + " " + str(int(minute)).zfill(2) + "."+ str(int(second)).zfill(2))

		if(0.0 != duration):
			self.enable_zone(self.current_zone_index)
		else:
			self.log("Skipping valve "+ str(self.current_zone_index+1))

		if(self.zone_count == self.current_zone_index+1):
			self.current_handle = self.run_at(self.stop_cycle, target_time)
		else:
			self.current_handle = self.run_at(self.next_zone, target_time)

	def enable_zone(self, zone_index):
		self.log("Opening valve " + self.zones_id[zone_index])
		self.turn_on(self.zones_id[zone_index])

	def disable_zone(self, zone_index):
		self.log("Closing valve " + self.zones_id[zone_index])
		self.turn_off(self.zones_id[zone_index])

	def stop_cycle(self, kwargs):
		#will run at {date} cycle status
		self.cancel_timer(self.current_handle)
		self.disable_zone(self.current_zone_index)
		self.current_zone_index = -1
		self.log("Cycle Stopped")
		self.turn_off(self.cycle_running_id)
		self.calculate_next_time()

	def set_cycle_status(self, status):
		self.set_textvalue(self.cycle_status_id, status)
