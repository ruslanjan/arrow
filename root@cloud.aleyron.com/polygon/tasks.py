from arrow.celery import app

# class Config:
#     def __init__(self,
#                  container_wall_time_limit: int,
#                  wall_time_limit: int,
#                  time_limit: int,
#                  memory_limit: int,
#                  files: dict,
#                  run_command: str,):
#         self.container_wall_time_limit = container_wall_time_limit
#         self.wall_time_limit = wall_time_limit
#         self.time_limit = time_limit
#         self.memory_limit = memory_limit
#         self.files = files
#         self.run_command = run_command
from .models import Submission, Test

check_post_script = '''
#!/bin/bash
g++ -std=c++17 -static -o solution solution.cpp > checker_output
g++ -std=c++17 -static -o checker checker.cpp > checker_output

touch checker_output_file
./solution < usercode/input_file > answer_file
./checker usercode/input_file usercode/output_file answer_file checker_output_file
printf $? > checker_result_file

printf \"checker_result@checker_result_file\\n\" >> payload_files
printf \"checker_output@checker_output_file\\n\" >> payload_files
printf \"generator_errors@generator_errors_file\\n\" >> payload_files
printf \"compilation_errors@compilation_errors_file\\n\" >> payload_files
'''


def python3_submission(submission, test):
    return {
        "container_wall_time_limit": 300,  # for whole execution
        "wall_time_limit": 10,  # for isolate
        "time_limit": submission.problem.time_limit,
        "memory_limit": submission.problem.memory_limit,
        "files": {
            "usercode/code.py": str(submission.data),
            "solution.cpp": str(submission.problem.solution),
            "checker.cpp": str(submission.problem.checker),
            "prepare.sh": '''''',
            "usercode/input_file": str(test.data),
            "post.sh": check_post_script
        },
        "run_command": '/usr/bin/python3 code.py'
    }


def cpp17_submission(submission, test):
    if not test.use_generator:
        return {
            "container_wall_time_limit": 300,
            "wall_time_limit": 10,  # for isolate
            "time_limit": submission.problem.time_limit,
            "memory_limit": submission.problem.memory_limit,
            "files": {
                "code.cpp": str(submission.data),
                "solution.cpp": str(submission.problem.solution),
                "checker.cpp": str(submission.problem.checker),
                "prepare.sh": '''
                #!/bin/bash
                touch generator_errors_file
                touch compilation_errors_file
                g++ -std=c++17 -static -o usercode/a.out code.cpp | tee prepare_errors compilation_errors_file
                ''',
                "usercode/input_file": str(test.data),
                "post.sh": check_post_script
            },
            "run_command": './a.out'
        }
    else:
        return {
            "container_wall_time_limit": 300,
            "wall_time_limit": 10,  # for isolate
            "time_limit": submission.problem.time_limit,
            "memory_limit": submission.problem.memory_limit,
            "files": {
                "code.cpp": str(submission.data),
                "solution.cpp": str(submission.problem.solution),
                "checker.cpp": str(submission.problem.checker),
                "gen.cpp": str(test.generator.generator),
                "prepare.sh": '''
                #!/bin/bash
                touch generator_errors_file
                touch compilation_errors_file
                g++ -std=c++17 -static -o usercode/a.out code.cpp | tee prepare_errors compilation_errors_file
                g++ -std=c++17 -static -o gen gen.cpp | tee prepare_errors  generator_errors_file
                ./gen {} > usercode/input_file
                '''.format(test.data),
                "usercode/input_file": str(test.data),
                "post.sh": check_post_script
            },
            "run_command": './a.out'
        }

@app.task
def prepare_sandbox_config_for_submission(submission_id, test_id):
    submission = Submission.objects.get(pk=submission_id)
    if not submission.testing:
        submission.testing = True
        submission.save()
    test = Test.objects.get(pk=test_id)
    problem = submission.problem

    run_configs = {
        'PYTHON3': python3_submission,
        'CPP17': cpp17_submission
    }

    run_config = run_configs[submission.submission_type](submission, test)

    return run_config


@app.task
def prepare_sandbox_config_for_submission_on_error(request, exc, traceback,
                                                   submission_id, test_id):
    print('Task {0!r} raised error: {1!r}'.format(request.id, exc))
    submission = Submission.objects.get(pk=submission_id)
    if submission:
        submission.testing = False
        submission.tested = True
        submission.verdict = submission.TE
        submission.verdict_message = f'Test failed :('
        submission.save()


@app.task
def run_sandbox(config):
    """
    DO NOT CALL THIS TASK DIRECTLY.
    TODO: Implement local dev execution (not safe one)
    should be implemented in worker
    accepts json
    like that
    {
        "container_wall_time_limit": 300,
        "wall_time_limit": 10,
        "time_limit": 1,
        "memory_limit": 256000,
        "files": {
            "usercode/file.py": "print(input())",
            "prepare.sh": "",
            "usercode/input_file": "123",
            "post.sh": "#!/bin/bash\nprintf \"output@usercode/output_file\\nerror_file@usercode/error_file\" > payload_files"
        },
        "run_command": "/usr/bin/python3 file.py"
    }
    returns
    data = {
            'payload': {},
            'prepare_logs': prepare_logs,
            'prepare_errors': prepare_errors,
            'logs': logs,
            'meta': parsed_meta,
            'IE': False
        }
    where payload contains files you provided in
    see arrow worker for more docs
    """
    print('error')


@app.task
def parse_sandbox_result(result, submission_id, test_id):
    test = Test.objects.get(pk=test_id)
    print(result)
    return {
        'checker_result': result['payload']['checker_result'],
        'checker_message': result['payload']['checker_output'],
        'prepare_errors': result['prepare_errors'],
        'generator_errors': result['payload']['generator_errors'],
        'compilation_errors': result['payload']['compilation_errors'],
        'meta': result['meta'],
        'test_id': test_id,
        'test_index': test.index
    }


@app.task
def apply_submission_result_for_submission(verdicts, submission_id):
    print(verdicts)
    verdicts = sorted(verdicts, key=lambda k: k['test_index'])
    submission = Submission.objects.get(pk=submission_id)
    submission.tested = True
    if None in verdicts:
        submission.verdict = submission.TE
        submission.save()
        return
    meta_status = {
        'RE': Submission.RE,
        'TO': Submission.TLE,
        'SG': Submission.MLE,
        'XX': Submission.TE,
    }
    meta_status_verbose = {
        'RE': 'Runtime error',
        'TO': 'Time limit exceeded',
        'SG': 'Memory limit exceeded',
        'XX': 'Test error',
    }
    for verdict in verdicts:
        meta = verdict['meta']
        if 'status' in verdict['meta']:
            if verdict['meta']['status'] in meta_status:
                submission.verdict = meta_status[verdict['meta']['status']]
                submission.verdict_message = \
                    f'{meta_status_verbose[verdict["meta"]["status"]]} on test #{verdict["test_index"]}'
                submission.save()
                return
            if verdict['generator_errors']:
                submission.verdict = Submission.TE
                submission.verdict_message = f'Test error.'
                submission.verdict_debug_message = f'Test error. Generator failed'
                submission.verdict_debug_description = verdict['generator_errors']
                submission.save()
                return
            if verdict['compilation_errors']:
                submission.verdict = Submission.CP
                submission.verdict_message = f'Compilation error'
                submission.verdict_description = verdict['compilation_errors']
                submission.save()
                return

    verdict_dict = {
        0: Submission.OK,
        1: Submission.WA,
        2: Submission.PE,
    }
    verbose = {
        0: 'Accepted',
        1: 'Wrong answer',
        2: 'Presentation error',
    }
    for verdict in verdicts:
        checker_result = verdict['checker_result']
        if not checker_result.isnumeric():
            submission.verdict = Submission.TE
            submission.verdict_message = f'Test error on test #{verdict["test_index"]}'
            submission.save()
            return
        checker_result = int(checker_result)
        if checker_result != 0:
            if checker_result in verdict_dict:
                submission.verdict = verdict_dict[checker_result]
                submission.verdict_message = f'{verbose[checker_result]} on test #{verdict["test_index"]}'
                submission.save()
                return
            else:
                submission.verdict = Submission.UNKNOWN_CODE
                submission.verdict_message = f'{verbose[checker_result]} on test #{verdict["test_index"]}'
                submission.save()
                return
    submission.verdict = Submission.OK
    submission.verdict_message = f'{verbose[0]}'
    submission.save()
