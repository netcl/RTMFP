import re
import os
from datetime import datetime

root_path = 'E:\\WORK\\RTMFP\\test\\'

class Readlog:
	def read(self):
		print('\tenter file name: ')
		input = raw_input()
		output = root_path + 'log_after_5min.txt'
		with open(root_path + input) as fr:
			begin = ''
			with open(output, 'a+') as fw:
				for line in fr:
					tmp = re.split("\s+", line)
					#print tmp[3]
					tmp_time = re.split("[\.]", tmp[3])
					t = datetime.strptime(tmp_time[0], '%H:%M:%S')
					if begin == '':
						begin = t						
					else:
						gaptime = (t - begin).seconds
						if gaptime >= 300:
							fw.write(line)
		

class Download_peer:
	def get_all_peer(self):
		print '\tenter input file: '
		input_file = raw_input()
		output = root_path + 'all_peer.txt'
		with open(root_path + input_file) as fr:
			with open(output, 'a+') as fw:
				data = fr.readline()
				while data:
					if re.search(' end', data) is not None:
						break
					if re.search('recv', data) is not None:
						next = fr.readline()
						if re.search('SesionProcessInput', next) is not None:
							two_line = data + next					
							result = self.find_info(two_line)
							if result != '':
								fw.write(result + '\n')
					if re.search('createPacket', data) is not None:
						next = fr.readline()
						if re.search('send', next) is not None:
							two_line = data + next
							result = self.find_info(two_line)
							if result != '':
								fw.write(result + '\n')
					data = fr.readline()
						
	def find_info(self, two_line):
		pattern_recv = re.search('(\d+:\d+:\d+.\d+).+addr:\"(\d+.\d+.\d+.\d+:\d+)\".*\n.+sequenceNumber:(\d+),fsnOffset:(\d+).+', two_line)
		pattern_send = re.search('(\d+:\d+:\d+.\d+).+AckRanges:\{(\w+);.*\n.+addr:\"(\d+.\d+.\d+.\d+:\d+)\"', two_line)
		strout = ''
		if pattern_recv is not None:
			tmp = pattern_recv.group()
			bytes = re.findall('length:(\d+)', tmp)
			total_byte = 0
			for byte in bytes:
				total_byte += int(byte)
			strout = pattern_recv.group(1) + "   " + pattern_recv.group(2) + "	 " + pattern_recv.group(3) + "   " + pattern_recv.group(4) + "	 " + str(total_byte)
		if pattern_send is not None:
			strout = pattern_send.group(1) + "	" + pattern_send.group(3) + "   " + pattern_send.group(2)
		return strout 
				
		
	def cacl_one_peer(self):
		print '\tenter peer: '
		peer = raw_input()
		print '\tenter input: '
		input_file = raw_input()
		peer_copy = peer.replace(':', '.')
		output_fsn_sn = root_path  + peer_copy + '_fsn_sn.txt'
		output_peer = root_path + peer_copy + '_peer.txt'
		output_loss_retrans = root_path + peer_copy + '_loss_retrans.txt'
		with open(root_path + input_file ) as fr:
			with open(output_fsn_sn, 'a+') as fw:
				with open(output_peer, 'a+') as peer_w:
					#record the first line
					num = 0
					for line in fr:
						seq_line = re.split('\s+', line)
						cur_peer = seq_line[1]
						if cur_peer == peer:
							peer_w.write(line)
							if 'cumack' not in line: # seq line																											
								seqnum = seq_line[2]
								fsnoffset = seq_line[3]
								if num == 0:
									begin_time = seq_line[0]
									num += 1
								cur_time = seq_line[0]
								gap_time = Download_peer.deal_time(cur_time, begin_time)
								fw.write(str(gap_time) + '\t' + seqnum + '\t' + fsnoffset + '\t' + str(int(seqnum) - int(fsnoffset)) + '\n')										
		self.cacl_one_peer_loss_retrans(output_peer, output_loss_retrans, peer)
		return 0
		
	def cacl_one_peer_loss_retrans(self, input, output, peer):
		#print input
		#print output
		#raw_input()
		with open(input) as fr:
			with open(output, 'a+') as fw:
				begin_time, tag = '', ''
				seq_line, missing, send = [], [], []
				total_num, miss_num, retrans_num = 0, 0, 0
				for line in fr:				
					if 'cumack' not in line: #seq line                  
						tag = '0'
						cur_time, peer, seq = Download_peer.parse_seq_line(line)
					else: #cumack line
						tag = '1'
						cur_time, peer, cumack, missed, received = Download_peer.parse_cumack_line(line)
					if begin_time == '':
						begin_time = cur_time
					gap_time = Download_peer.deal_time_second(cur_time, begin_time)
					if gap_time <= 10:
						if tag == '0':
							seq_line.append(int(seq))
							if int(seq) in missing:
								#print '\t', seq
								retrans_num += 1
						if tag == '1':
							#print missed
							if len(missed) != 0:
								for k in missed:
									if '..' in k: # many missing seq
										#print missed
										many_seq = re.split('\.\.', k)
										left, right = int(many_seq[0]), int(many_seq[1])
										gap_seq = right - left + 1										
										for i in range(gap_seq):
											if (left + i) not in missing:
												missing.append(left + i)
												#print left + i
												miss_num += 1
										#print miss_num
										#raw_input()
									else: # one missing
										if int(k) not in missing:
											missing.append(int(k))
											#print k
											miss_num += 1
								#print miss_num
								#raw_input()
							if len(received) == 0:
								send.append(int(cumack))
							else: # have received
								k = received[-1]
								#print received[-1]
								if '..' in k: # many received
									right = re.split('\.\.', k)[-1]									
									send.append(int(right))
								else: # one received									
									send.append(int(k))							
					else:
						#write info
						#print send
						#print seq_line
						#print missing
						total_num = retrans_num + send[-1] - send[0]
						print 'send', send[-1], send[0]
						if send[-1] - send[0] < 0:
							raw_input()
						if seq_line[-1] > send[-1]:
							total_num += 1
						fw.write(str(total_num) + '\t' + str(miss_num) + '\t' + str(retrans_num) + '\n')
						# init info
						begin_time = cur_time
						total_num, miss_num, retrans_num = 0, 0, 0
						send, seq_line = [], []
						#raw_input()
    
	def one_peer(self, input, u_peer, begin_num, read_num):
		#print input
		#print begin_time, end_time
		with open(input) as fr:
			tag = ''
			seq_line, missing, send = [], [], []
			total_num, miss_num, retrans_num = 0, 0, 0
			cur_read = 0
			for line in fr:	
				cur_read += 1
				if cur_read < begin_num:
					continue
				else:
					if (cur_read - begin_num) <= read_num:
						#print cur_read, u_peer
						if 'cumack' not in line: #seq line                  
							tag = '0'
							cur_time, peer, seq = Download_peer.parse_seq_line(line)
						else: #cumack line
							tag = '1'
							cur_time, peer, cumack, missed, received = Download_peer.parse_cumack_line(line)
						if peer == u_peer: # same peer
							#print u_peer, peer
							#print cur_time, begin_time						
							if tag == '0':
								seq_line.append(int(seq))
								if int(seq) in missing:
									#print '\t', seq
									retrans_num += 1
							if tag == '1':
								#print missed
								if len(missed) != 0:
									for k in missed:
										if '..' in k: # many missing seq
											#print missed
											many_seq = re.split('\.\.', k)
											left, right = int(many_seq[0]), int(many_seq[1])
											gap_seq = right - left + 1										
											for i in range(gap_seq):
												if (left + i) not in missing:
													missing.append(left + i)
													#print left + i
													miss_num += 1
											#print miss_num
											#raw_input()
										else: # one missing
											if int(k) not in missing:
												missing.append(int(k))
												#print k
												miss_num += 1
									#print miss_num
									#raw_input()
								if len(received) == 0:
									send.append(int(cumack))
								else: # have received
									k = received[-1]
									#print received[-1]
									if '..' in k: # many received
										right = re.split('\.\.', k)[-1]									
										send.append(int(right))
									else: # one received									
										send.append(int(k))
					else:
						break
			if len(send) == 0:
				return 0, 0, 0
			total_num = retrans_num + send[-1] - send[0]
			print(len(send))
			if send[-1] - send[0] < 0:
				print send, u_peer
				i = len(send) - 1
				while i >= 0:
					if send[i] >= send[0]:
						total_num = retrans_num + send[i] - send[0]
						print send[i]
						break
					i -= 1
				raw_input()
			if len(send) > 0 and len(seq_line) > 0:
				if seq_line[-1] > send[-1]  :
					total_num += 1
			return total_num, miss_num, retrans_num

	@staticmethod
	def deal_time_second(cur_time, begin_time):		
		cur = datetime.strptime(re.split('\.', cur_time)[0], '%H:%M:%S')
		begin = datetime.strptime(re.split('\.', begin_time)[0], '%H:%M:%S')
		gap = (cur - begin).seconds
		# get ms
		return gap
		
	@staticmethod
	def deal_time(cur_time, begin_time):
		cur = re.split('[:\.]', cur_time)
		begin = re.split('[:\.]', begin_time)		
		h = int(cur[0]) - int(begin[0])		
		m = int(cur[1]) - int(begin[1])		
		s = int(cur[2]) - int(begin[2])		
		ms = int(cur[3]) - int(begin[3])
		return str(h * 3600 * 1000 + m * 60 * 1000 + s * 1000 + ms)
	
	@staticmethod
	def parse_seq_line(line):
		data = re.split('\s+', line)
		time, peer, seq, fsnoffset = data[0], data[1], data[2], data[3]
		return time, peer, seq
		
	@staticmethod
	def parse_cumack_line(line):
		data = re.split('\s+', line)
		time, peer, ackrange = data[0], data[1], data[2]
		cumack = re.split(':', data[3])[1]
		missed = re.findall('missing (\d+\.\.\d+|\d+)', line)
		received = re.findall('received (\d+\.\.\d+|\d+)', line)
		return time, peer, cumack, missed, received
		
	def cacl_all_peer(self):
		print '\tenter input: '
		input_file = raw_input()
		output = root_path + 'all_peer_10s_loss_retrans.txt'
		with open(root_path + input_file) as fr:
			with open(output, 'a+') as fw:
				begin_time = ''
				map_cacl = {}
				begin_num = 1
				read_num = 0
				for line in fr:
					data = re.split('\s+', line)
					peer = data[1]
					if peer not in map_cacl:
						map_cacl[peer] = []
					cur_time = data[0]
					if begin_time == '':
						begin_time = cur_time
					#print cur_time, begin_time
					gap_time = Download_peer.deal_time_second(cur_time, begin_time)
					if gap_time <= 10:
						last_time = cur_time
						read_num += 1
					else:
						print gap_time
						end_time = last_time
						for key in map_cacl:
							#print self.one_peer(root_path + input_file, key, begin_time, end_time)
							r1, r2, r3 = self.one_peer(root_path + input_file, key, begin_num, read_num)
							map_cacl[key].append(r1)
							map_cacl[key].append(r2)
							map_cacl[key].append(r3)
						begin_time = cur_time
						begin_num += read_num
						read_num = 0
						total_send, total_miss, total_retrans = 0, 0, 0
						#print map_cacl
						for key in map_cacl:
							total_send += map_cacl[key][0]
							total_miss += map_cacl[key][1]
							total_retrans += map_cacl[key][2]
						fw.write(str(total_send) + '\t' + str(total_miss) + '\t' + str(total_retrans) + '\n')
						fw.flush()
						map_cacl = {}
					
class Ackrange:
	def cacl(self):
		print('\tenter input file: ')
		input_file = raw_input()
		output = root_path + 'parse_ackrange.txt'
		peer_list = {}
		with open(root_path + input_file) as fr:
			with open(output, 'a+') as fw:
				for line in fr:
					tmp = re.split('\s+', line)
					size = len(tmp)
					#print size
					if size == 4:
						#print tmp[2]
						strr = self.parse_ackrange(tmp[2])
						#print strr
						fw.write(line.strip('\n') + '\t' + 'cumack:' + str(strr[0]) + '\t' + strr[1] + '\n')
					else:
						peer = tmp[1]
						byte = int(tmp[4])
						if peer not in peer_list:
							peer_list[peer] = 0
						peer_list[peer] += byte
						fw.write(line)
		output_all_peer = root_path + 'peer_list.txt'
		with open(output_all_peer, 'a+') as fw:
			# traffic sorted reverse
			result = sorted(peer_list.iteritems(), key = lambda x:x[1], reverse = True)
			for peer in result:
				fw.write(peer[0] + '\t' + str(peer[1]) + '\n')				

	def parse_ackrange(self, str):
		length = len(str)
		seqnum = 0
		strr = ''
		if length <= 6 or str[2:4] == "00" :#this is flow exception
			return seqnum, strr
		if str[6] < '8' :#two valid place
			seqnum = int(str[6:8], 16)
			index = 8
			strr = self.my_loop(index, seqnum, strr, str)	
		if str[6] >= '8' and ((length - 10) % 4 == 0):#four valid place
			a = int(str[6:8], 16)
			a1 = (a - 128) * 128
			b = int(str[8:10], 16)
			seqnum = a1 + b
			index = 10
			strr = self.my_loop(index, seqnum, strr, str)
		if str[6] >=  '8' and ((length - 12) % 4 == 0):#six valid place
			a = int(str[6:8], 16)
			b = int(str[8:10], 16)
			c = int(str[10:12], 16)
			a1 = (a - 128) * 128 * 128
			b1 = (b - 128) * 128
			seqnum = a1 + b1 + c
			index = 12
			strr = self.my_loop(index, seqnum, strr, str)
		return seqnum, strr
		
	def my_print(self, seqnum, holes, received):
		str1 = "holes=" + str(holes)
		str2 = "received=" + str(received)		
		if holes == 1:
			#print"missing",seqnum+holes,
			str3 = "missing " + str(seqnum + holes)
		else:
			#print"missing",seqnum+1,"..",seqnum+holes,
			str3 = "missing " + str(seqnum + 1) + ".." + str(seqnum + holes)
		if received == 1:
			#print"received",seqnum+holes+received
			str4 = "received " + str(seqnum + holes + received)
		else:
			#print"received",seqnum+holes+1,"..",seqnum+holes+received
			str4 = "received " + str(seqnum + holes + 1) + ".." + str(seqnum + holes + received)
		str5 = str1 + " " + str2 + " " + str3 + " " + str4
		return str5
	
	def my_loop(self, index, seqnum, strr, str):
		#print str
		while str[index:] != '':
				holes = int(str[index:index + 2], 16) + 1
				received = int(str[index + 2:index + 4], 16) + 1
				strr = strr + ' ' + self.my_print(seqnum, holes, received)
				seqnum += holes + received
				index += 4
		return strr
		
def readlog():
	readlog = Readlog()
	readlog.read()
	
def get_all_peer():
	dl = Download_peer()
	dl.get_all_peer()

def cacl_ackrange():
	ackrange = Ackrange()
	ackrange.cacl()

def cacl_one_peer():
	dl = Download_peer()
	dl.cacl_one_peer()

def cacl_all_peer():
	dl = Download_peer()
	dl.cacl_all_peer()

	
def main():
	id = 0
	id_function = {'1':readlog, '2':get_all_peer, '3':cacl_ackrange, '4':cacl_one_peer, '5':cacl_all_peer}
	#line = '19:16:27.340	122.6.197.37:33017   02ff7fdd3b	cumack:11963'
	#Download_peer.parse_cumack_line(line)
	#cur_time = '19:16:59.149'
	#begin_time = '19:16:1.275'
	#print Download_peer.deal_time_second(cur_time, begin_time)
	while True:
		print '**********************************************'
		print '\t1: readlog and get data after 5 minutes'
		print '\t2: get all download peer info'
		print '\t3: cacl ackrange'
		print '\t4: cacl one peer sn fsn and loss retrans'
		print '\t5: cacl all peer loss retrans'
		print '\t6: exit'
		print '**********************************************'
		print '\tenter function id: '
		id = raw_input()
		if id in id_function:
			id_function[id]()
		if id == '6':
			break
	return 0

if __name__ == '__main__':
	main()